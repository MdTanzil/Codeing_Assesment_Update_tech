from django.db import models

# Create your models here.

class Order(models.Model):
    order_id = models.CharField(max_length=100)
    order_date = models.DateField()
    ship_date = models.DateField()
    ship_mode = models.CharField(max_length=100)
    customer_id = models.CharField(max_length=100)
    customer_name = models.CharField(max_length=100)
    segment = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=100)
    region = models.CharField(max_length=100)
    product_id = models.CharField(max_length=100)
    category = models.CharField(max_length=100)
    sub_category = models.CharField(max_length=100)
    product_name = models.CharField(max_length=256)
    sales = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.order_id
