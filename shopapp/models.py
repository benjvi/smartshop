from django.db import models

# Create your models here.  
class SupermarketBranch(models.Model):
    store_id = models.IntegerField(primary_key=True)
    store_location = models.CharField(max_length=100)
    
class Shopper(models.Model):
    email = models.EmailField(unique=True)
    tesco_pw = models.CharField(max_length=100)
    curr_sess_key = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    home_branch = models.ForeignKey(SupermarketBranch)
    customer_id = models.IntegerField(primary_key=True)
    # date/time when the product database that this shopper uses last was updated
    
class Department(models.Model):
    dept_id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=100)
    branch = models.ForeignKey(SupermarketBranch)
    
class Aisle(models.Model):
    aisle_id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=100)
    department = models.ForeignKey(Department)
        
class Shelf(models.Model):
    shelf_id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=100)
    aisle = models.ForeignKey(Aisle)
    
class Product(models.Model):
    name = models.CharField(max_length=100)
    prod_id = models.IntegerField(primary_key=True)
    image_url = models.URLField()
    
    #shelf = models.ForeignKey(Shelf)
    #'aisle = models.ForeignKey(Aisle)
    #department = models.ForeignKey(Department)
    #only the shelf field is strictly necessary - from this can retrieve aisle and department info
    shelves = models.ManyToManyField(Shelf)
    
    price = models.FloatField()
    price_per_calorie = models.FloatField(blank=True, null=True)
    on_offer = models.BooleanField(False)
    offertype = models.CharField(max_length=100)
    offerends = models.DateField(blank=True, null=True)
    brand = models.CharField(max_length=100)
    
    storage_info = models.CharField(max_length=100)
    product_weight_grams = models.IntegerField(blank=True, null=True)
    serving_size =  models.CharField(max_length=100)
    
    calories = models.IntegerField(blank=True, null=True)
    # can now calculate calories per serving size, which will indivate if the food is a complete meal, or a side 
    sugar_grams = models.FloatField(blank=True, null=True)
    fat_grams = models.FloatField(blank=True, null=True)
    sat_fat_grams = models.FloatField(blank=True, null=True)
    mono_unsat_fat_grams = models.FloatField(blank=True, null=True)
    poly_unsat_fat_grams = models.FloatField(blank=True, null=True)
    fibre_grams = models.FloatField(blank=True, null=True)
    salt_grams = models.FloatField(blank=True, null=True)
    sodium_grams = models.FloatField(blank=True, null=True)
    #technically, this will be the 'salt Equivalent'. This is a rescaling of the sodium intake in a given food, which is the measure that determines health outcomes
    
    product_rating = models.FloatField(blank=True, null=True)
    health_rating = models.FloatField(blank=True, null=True)
   
    
#NOTE - this should change with development. Things stored in the database should be in the final calculated, most useful, state