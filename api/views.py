from rest_framework import permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import CustomUserSerializer, OrderSerializer
from django.contrib.auth import authenticate, login
from rest_framework import viewsets
from .models import Order
from django.http import HttpResponse
from django.views import View
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from django.db.models import Count, Sum
from django.db.models.functions import ExtractYear
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import tempfile
import os
from io import BytesIO
import numpy as np
from decimal import Decimal


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = CustomUserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        user = authenticate(request, email=email, password=password)
        if user is not None:
            login(request, user)
            serializer = CustomUserSerializer(user)
            return Response(serializer.data)
        else:
            return Response({"error": "Invalid credentials"}, status=401)


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer


class GeneratePDFView(View):
    def get(self, request):
        # Generate the PDF report using ReportLab
        response = HttpResponse(content_type="application/pdf")

        # Create the PDF content
        pdf_buffer = BytesIO()
        doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)
        styles = getSampleStyleSheet()

        # print(orders_per_year)
        # Write the total number of orders count per year to the PDF
        content = []
        content.append(
            Paragraph("Total Number of Orders Count per Year", styles["Heading1"])
        )

        # Get the total number of orders count per year
        orders_per_year = Order.objects.values("order_date__year").annotate(
            count=Count("id")
        )

        for i in orders_per_year:
            # print(entry)
            year = i["order_date__year"]
            count = i["count"]
            content.append(Paragraph(f"In {year} order {count}", styles["Normal"]))
            content.append(Spacer(0.5, 12))
        content.append(Spacer(1, 12))
        content.append(
            Paragraph("Total Count of Distinct Customers", styles["Heading1"])
        )

        # Get the total count of distinct customers
        total_customers = Order.objects.values("customer_id").distinct().count()
        content.append(Paragraph(str(total_customers), styles["Normal"]))
        content.append(Spacer(1, 12))

        content.append(
            Paragraph("Top 3 Customers with Most Transactions", styles["Heading1"])
        )
        # Get the top 3 customers who have ordered the most with their total amount of transactions
        top_customers = (
            Order.objects.values("customer_id", "customer_name")
            .annotate(total_transactions=Sum("sales"))
            .order_by("-total_transactions")[:3]
        )

        for customer in top_customers:
            customer_name = customer["customer_name"]
            total_transactions = customer["total_transactions"]
            content.append(
                Paragraph(f"{customer_name}: {total_transactions}", styles["Normal"])
            )
            content.append(Spacer(0.5, 12))
        content.append(Spacer(1, 12))

        content.append(
            Paragraph(
                "Customer Transactions per Year (from the beginning year to last year)",
                styles["Heading1"],
            )
        )
        customer_transactions_per_year = (
            Order.objects.annotate(year=ExtractYear("order_date"))
            .values("year")
            .annotate(
                customer_count=Count("customer_id", distinct=True),
                total_sales=Sum("sales"),
            )
            .order_by("year")
        )
        for i in customer_transactions_per_year:
            year = i["year"]
            customer_count = i["customer_count"]
            total_sales = i["total_sales"]
            content.append(
                Paragraph(
                    f"Year :{year} , Customer Count: {customer_count} , Total Sales {total_sales}",
                    styles["Normal"],
                )
            )
            content.append(Spacer(0.5, 12))

        content.append(
            Paragraph(
                "Most Selling Items Sub-Category Names and Total Sales",
                styles["Heading1"],
            )
        )
        most_selling_subcategories = (
            Order.objects.values("sub_category")
            .annotate(total_sales=Sum("sales"))
            .order_by("-total_sales")
        )
        top_subcategories = most_selling_subcategories[:3]
        for i in top_subcategories:
            sub_category = i["sub_category"]
            total_sales = i["total_sales"]
            content.append(
                Paragraph(f"Name {sub_category},  total sale = {total_sales}")
            )
            content.append(Spacer(1, 12))

        city_sales = (
            Order.objects.values("state")
            .annotate(total_sales=Sum("sales"))
            .order_by("-total_sales")
        )
        city_data = [(entry["state"], entry["total_sales"]) for entry in city_sales]
        labels = [entry[0] for entry in city_data]
        sales = [entry[1] for entry in city_data]

        # Plot the pie chart
        plt.pie(sales, labels=labels, autopct="%1.1f%%")
        plt.title("Sales Performance by State")
        plt.axis("equal")
        content.append(Spacer(1, 12))
        # Save the chart as an image file
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
            image_path = temp_file.name
            plt.savefig(image_path, format="png")
        content.append(Spacer(1, 12))
        content.append(Spacer(1, 12))
        content.append(Spacer(1, 12))

        content.append(Paragraph("Sales Report", styles["Heading1"]))
        content.append(Spacer(1, 20))

        # Add the pie chart image
        image = Image(image_path, width=400, height=400)
        content.append(image)
        content.append(Spacer(1, 20))
        plt.close()
        # # Clean up the temporary image file
        # os.remove(image_path)

        sales_per_year = (
            Order.objects.annotate(year=ExtractYear("order_date"))
            .values("year")
            .annotate(total_sales=Sum("sales"))
            .order_by("year")
        )
        # print(sales_per_year)
        # Prepare the data for the line chart
        years = [i["year"] for i in sales_per_year]
        sales = [float(entry["total_sales"]) for entry in sales_per_year]

        # Plot the line chart
        plt.plot(years, sales)
        plt.xlabel("Year")
        plt.ylabel("Total Sales")
        plt.title("Sales Performance Over the Years")

        # Save the chart as an image file
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
            image_path = temp_file.name
            plt.savefig(image_path, format="png")

        # ...

        # Add the line chart image
        image2 = Image(image_path, width=400, height=400)
        content.append(image2)
        plt.close()

        # Build the report
        doc.build(content)
        os.remove(image_path)

        # Return the PDF as a response
        pdf_buffer.seek(0)
        response["Content-Disposition"] = 'attachment; filename="sales_report.pdf"'
        response.write(pdf_buffer.getvalue())

        return response
