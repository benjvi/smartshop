# Create your views here.
'''
Created on Nov 18, 2011

@author: Ben
'''
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.core.urlresolvers import reverse
from urllib2 import urlopen
from django.utils import simplejson
from django.db.models import Max, Min, Avg, Count, Q
from SmartShop.shopapp.models import *
import re

#for men (arbitrarily, but need to use consistent data)
rda_calories = 2600
rda_sat_fat_grams = 20
#GDA recommendation
rda_sugar_grams = 90
#GDA recommendation
rda_salt_grams = 6.0
#GDA recommendation
# rda_mono_unsat_fat_grams = 50
# this figure is as high an amount as possible to make up the total fat GDA of 70g
# some levels polyunsaturates and saturates maybe also necessary
# not a scientific/official figure
# need to do more research on what levels have been shown to have health benefits
# atm it seems like any potential health benefits are unproven
rda_fibre_grams = 18
rda_list = [rda_sat_fat_grams, rda_sugar_grams, rda_salt_grams, rda_fibre_grams]

# nb these arent all actual rdas - recommended min/max amounts as applicable

#mean amounts for men aged 19-64 in the UK (2011)
av_calories = 2255
av_sat_fat_grams = 30.0
av_sugar_grams = 112.0
av_salt_grams = 8.6
#av_mono_unsat_fat_grams = 29.3
#av_protein_grams = 88.4
av_fibre_grams = 12
av_amount_list = [av_sat_fat_grams, av_sugar_grams, av_salt_grams, av_fibre_grams]
error_codes = ""

def simplePage(request):
    # for the arrival page
    
    # provide a check if logged in function
    # better to user the django functinos here - dont get a persistant token to use with this API
    
    #then, just serves the page
    a=''
    # prep_meals = Aisle.objects.get(name="Chilled Food")
    for ai in Aisle.objects.all():
        a = a + '<p><strong>' + ai.name.__str__() + '</strong>'
        for s in Shelf.objects.all().filter(aisle=ai):
            a = a + '<p>' + s.name.__str__() + s.shelf_id.__str__()
            product_list = s.product_set.all()
            for product in product_list:
                a = a +'<p>'+'---'+product.name+': '+product.storage_info.__str__()+', ' \
                +'ID: '+product.prod_id.__str__()+ ", WEIGHT: " + product.product_weight_grams.__str__() + \
                 ' g, CALORIES:'+product.calories.__str__()+', SUGARS: ' +product.sugar_grams.__str__()+" g" \
                 +', FIBRE:'+product.fibre_grams.__str__()+' g, SATURATES:'+product.sat_fat_grams.__str__()+' g' 
                            #for p in Product.objects.all().filter(shelf=s):
         #   a = a +'<p><t>' + p.name.__str__()
    a=a+error_codes
    return HttpResponse(a)

def tescoLogin(request):
    # make a get request to the tesco rest service
    # TEST LINE
    email = 'ben881@gmail.com'    
    secret = ''
    
    #these should go into global variables (within this project!)
    devkey =  ''
    appkey = ''
    
    #make the login  request, and capture the result
    jsonuserfile = urlopen('https://secure.techfortesco.com/groceryapi_b1/restservice.aspx?command=LOGIN&email='+email+'&password='+secret+'&developerkey='+devkey+'&applicationkey='+appkey)
    
    # parse json to get the sessionkey. will need to use json libraries
    login_dict = simplejson.loads(jsonuserfile.read())

    supermarket = SupermarketBranch(login_dict['BranchNumber'])
    supermarket.save()
    
    try:
        shopper = Shopper.objects.all().get(email=email)
    except(ValueError, Shopper.DoesNotExist):
        #user does not already exist
        shopper = Shopper(email=email, tesco_pw=secret, curr_sess_key=login_dict['SessionKey'], name='', home_branch=supermarket, customer_id=login_dict['CustomerId'])
        shopper.save()
    else:
        #update session key
        shopper.curr_sess_key=login_dict['SessionKey']
        shopper.save()
        #TODO will also need to update other fields later
      
    #TODO at the moment this will add another entry to the database - which is bad
    #email should be a key
    #should update the details when the same user logs in again. 
                    
    #categories_dict = simplejson.loads(jsoncategoriesfile.read())
    #department_id = categories_dict['Id']
    
    #if the user's branch has not been synced before/recently, then do this
    #syncTescoData(shopper, supermarket)
    # LETS NOT DO THIS EVERY TIME WE LOGIN!
    #b = gatherProductInfo(shopper)
    
    a=''
    for d in Shelf.objects.all():
        a = a + '<p>' + d.name 
        
    return HttpResponse(a)
   
    # go on to use the session key to request some initial data from the api
    # this is also an external function
    # add the asynchronous database update here later

def getDetails(request):
    #need to be logged-in first
    shopper = Shopper.objects.get(email='ben881@gmail.com')
    supermarket = shopper.home_branch
    syncProductDetails(shopper, supermarket)
    
    return HttpResponseRedirect(reverse(simplePage))

def syncProductDetails(shopper, supermarket):
    #TODO choose a subset of these products - so that this doesn't take hours to complete
    for product in Product.objects.all():
        try:
            retrieveProductExtendedDetails(product, shopper)
        except(ValueError):
            continue
        except(IndexError):
            break

def getJSON(request):
    shopper = Shopper.objects.get(email='ben881@gmail.com')
    supermarket = shopper.home_branch
    shelf = Shelf.objects.all().get(shelf_id=111)
    #json_products_file = urlopen('http://www.techfortesco.com/groceryapi_b1/restservice.aspx?command=LISTPRODUCTSBYCATEGORY&category='+ \
    #                          shelf.shelf_id.__str__() +'&sessionkey='+ shopper.curr_sess_key + '&EXTENDEDINFO=Y')
    product_list = Product.objects.all().filter(shelf=shelf)
    json_oneprod_file = urlopen('http://www.techfortesco.com/groceryapi_b1/restservice.aspx?command=PRODUCTSEARCH&searchtext='+ \
                                    "255956929" +'&sessionkey='+ shopper.curr_sess_key.__str__() + '&EXTENDEDINFO=Y')
    #product_list[5].prod_id.__str__()
    output = json_oneprod_file.read()
    return HttpResponse(output)

def getProductJSON(request, product):
    shopper = Shopper.objects.get(email='ben881@gmail.com')
    #json_products_file = urlopen('http://www.techfortesco.com/groceryapi_b1/restservice.aspx?command=LISTPRODUCTSBYCATEGORY&category='+ \
    #                          shelf.shelf_id.__str__() +'&sessionkey='+ shopper.curr_sess_key + '&EXTENDEDINFO=Y')
    json_oneprod_file = urlopen('http://www.techfortesco.com/groceryapi_b1/restservice.aspx?command=PRODUCTSEARCH&searchtext='+ \
                                    product +'&sessionkey='+ shopper.curr_sess_key.__str__() + '&EXTENDEDINFO=Y')
    #product_list[5].prod_id.__str__()
    output = json_oneprod_file.read()
    return HttpResponse(output)

def updateProductDetails(request, product):
    shopper = Shopper.objects.get(email='ben881@gmail.com')
    product_objs = Product.objects.all().filter(prod_id=product)
    a=''
    for product in product_objs:
        retrieveProductExtendedDetails(product, shopper)
        a = a+ '<p>'+'---'+product.name+': '+product.storage_info.__str__()+', ' \
                        +'ID: '+product.prod_id.__str__()+ ", WEIGHT: " + product.product_weight_grams.__str__() + \
                         ' g, CALORIES:'+product.calories.__str__()+', SUGARS: ' +product.sugar_grams.__str__()+" g" \
                         +', FIBRE:'+product.fibre_grams.__str__()+' g, SATURATES:'+product.sat_fat_grams.__str__()+' g' \
                         + ', SHELF: ' + product.shelves.all()[0].name
    return HttpResponse(a)                 
    

def calculateMetrics(request, product_id):
    product = Product.objects.all().filter(prod_id=product_id)[0]
    calcProductHealthRating(product)
    calcPricePerCalorie(product)
    out_string = product.name+", HEALTH RATING: "+product.health_rating.__str__()+ \
                    ", PRICE PER CALORIE:"+product.price_per_calorie.__str__()
    return HttpResponse(out_string)

def calculateAllMetrics(request):
    product_list = Product.objects.all().filter(~Q(fibre_grams=None)&~Q(sat_fat_grams=None)&~Q(sugar_grams=None)&~Q(salt_grams=None))
    out_string=""
    for product in product_list:
        calcProductHealthRating(product)
        calcPricePerCalorie(product)
        out_string = out_string +"<p>"+product.name+", HEALTH RATING: "+product.health_rating.__str__()+ \
                    ", PRICE PER CALORIE:"+product.price_per_calorie.__str__()
    return HttpResponse(out_string)

def foodStatistics(request):
    #retreive list of products that have all the nutritional information
    query = ~Q(fibre_grams=None)&~Q(sat_fat_grams=None)&~Q(sugar_grams=None)&~Q(salt_grams=None)&~Q(health_rating=None)
    product_list = Product.objects.all().filter(~Q(fibre_grams=None)&~Q(sat_fat_grams=None)&~Q(sugar_grams=None)&~Q(health_rating=None)&~Q(salt_grams=None))
    
    num_products = product_list.count()
    #find healthiest product, unhealthiest product
    healthiest_rating = product_list.aggregate(Max('health_rating'))
    unhealthiest_rating = product_list.aggregate(Min('health_rating'))
    
    avg_health_rating = product_list.aggregate(Avg('health_rating'))
    
    #also, most exp/cheapest
    highest_exp = product_list.aggregate(Max('price_per_calorie'))
    
    lowest_exp = product_list.aggregate(Min('price_per_calorie'))
    
    avg_price = product_list.aggregate(Avg('price_per_calorie'))
    #
    output_health_str=""
    output_unhealth_str=""
    output_exp_str=""
    output_cheap_str=""
    for i in range(10):
        healthiest_product = product_list.order_by('health_rating')[num_products-(i+1)]
        unhealthiest_product = product_list.order_by('health_rating')[i]
        output_health_str = output_health_str+'<p>'+'Healthiest Product(#'+(i+1).__str__()+'):'+healthiest_product.name+', ID: '+healthiest_product.prod_id.__str__() \
                    +', Rating: '+healthiest_product.health_rating.__str__() \
                    +', Price Per Calorie'+healthiest_product.price_per_calorie.__str__() 
        output_unhealth_str = output_unhealth_str+'<p>'+'Unhealthiest Product(#'+(i+1).__str__()+'):'+unhealthiest_product.name+', ID: '+unhealthiest_product.prod_id.__str__() \
                    +', Rating: '+unhealthiest_product.health_rating.__str__() \
                    +', Price Per Calorie'+unhealthiest_product.price_per_calorie.__str__() 
         #           +'<p>'+'Average Health Product:'+avg_health_product.name+', ID: '+avg_health_product.prod_id.__str__()+ \
         #           +', Rating: '+avg_health_product.health_rating.__str__()+\
         #           ', Price Per Calorie'+avg_health_product.price_per_calorie.__Str__()
        expensive_product = product_list.order_by('price_per_calorie')[num_products-(i+1)]
        cheapest_product = product_list.order_by('price_per_calorie')[i]
        output_exp_str = output_exp_str+'<p>'+'Most Expensive Product(#'+(i+1).__str__()+'):'+expensive_product.name+', ID: '+expensive_product.prod_id.__str__() \
                    +', Rating: '+expensive_product.health_rating.__str__() \
                    +', Price Per Calorie'+expensive_product.price_per_calorie.__str__() 
        output_cheap_str = output_cheap_str+'<p>'+'Cheapest Product(#'+(i+1).__str__()+'):'+cheapest_product.name+', ID: '+cheapest_product.prod_id.__str__() \
                    +', Rating: '+cheapest_product.health_rating.__str__() \
                    +', Price Per Calorie'+cheapest_product.price_per_calorie.__str__() 
        #            +'<p>'+'Average Health Product:'+avg_price_product.name+', ID: '+avg_price_product.prod_id.__str__()+ \
        #            +', Rating: '+avg_price_product.health_rating.__str__()+\
        #            ', Price Per Calorie'+avg_price_product.price_per_calorie.__Str__()           
    output_count_str = '<p>'+'Number of products with complete info:'+num_products.__str__()
    return HttpResponse(output_count_str+output_health_str+output_unhealth_str+output_exp_str+output_cheap_str)
                
    
def syncTescoData(shopper, supermarket):    
    #THIS IS THE MAIN JSON PARSING FUNCTION RIGHT HERE
    jsoncategoriesfile = urlopen('http://www.techfortesco.com/groceryapi_b1/restservice.aspx?command=LISTPRODUCTCATEGORIES&sessionkey='+shopper.curr_sess_key)
    categories_dict = simplejson.loads(jsoncategoriesfile.read())
    for TopLevelNode, Value in categories_dict.iteritems():
        # have a "StatusCode", a "StatusInfo", and "Departments"
        if (TopLevelNode=='Departments'):         #TODO - is this a robust way to do this?
            # department_dict = simplejson.loads(Value)
            ListOfDepartments = Value
            for J_Dept in ListOfDepartments:
                #Department is a dict
                jSONDeptParse(J_Dept, supermarket)
    return
    
def jSONDeptParse(J_Dept, supermarket):
    #in a Department, the section_compt is the aisles, in an Aisle it is the shelves
    temp_id, temp_name = '',''
    for Key, Value in J_Dept.iteritems():
        if (Key=='Id'):
            temp_id = Value
        elif (Key=='Name'):
            temp_name = Value
                   
    dept = Department(dept_id=temp_id, name=temp_name, branch=supermarket)
    dept.save()
    for Key, Value in J_Dept.iteritems():
        if (Key=='Aisles'):
            for J_Aisle in Value:
                jSONAisleParse(J_Aisle, dept)
    return
                
def jSONAisleParse(J_Aisle, dept):     
    #in a Department, the section_compt is the aisles, in an Aisle it is the shelves
    temp_id, temp_name = '',''
    for Key, Value in J_Aisle.iteritems():
        if (Key=='Id'):
            temp_id = Value
        elif (Key=='Name'):
            temp_name = Value
                   
    aisle = Aisle(aisle_id=temp_id, name=temp_name, department=dept)
    aisle.save()
    for Key, Value in J_Aisle.iteritems():
        if (Key=='Shelves'):
            for J_Shelf in Value:
                jSONShelfParse(J_Shelf, aisle)
    return

def jSONShelfParse(J_Shelf, aisle):
    temp_id, temp_name = '',''
    for Key, Value in J_Shelf.iteritems():
        if (Key=='Id'):
            temp_id = Value
        elif (Key=='Name'):
            temp_name = Value
                   
    shelf = Shelf(shelf_id=temp_id, name=temp_name, aisle=aisle)
    shelf.save()
    
    #ALGORITHM TO GATHER PRODUCT INFO COULD GO HERE
    
    return
        
def gatherProductInfo(shopper):
    
    #this comes after we have parsed all the relevant shelves, aisles and departments
    #in fact, this could be used from anywhere in the program with a logged-in user
    aisle_names = ['Chilled Ready Meals']
    #,'Chilled Food', 'Pasta Rice & Noodles', 'Cooking Sauces & Meal kits',
    #              'Frozen Ready Meals', 'Frozen Pies & Quiches', 'Frozen Pizza & Garlic Bread', 
    #              'Frozen Meat Free & Vegetarian
    
    aisle_list = []
    for name in aisle_names:
        temp_aisle = Aisle.objects.all().get(name=name)
        aisle_list.append(temp_aisle)
    #select a subset of department and aisles that are relevant to what I want to do, ie the food ones, and get the extended product info for those ones
    for sel_aisle in aisle_list:
        for sel_shelf in Shelf.objects.all().filter(aisle=sel_aisle):
            # sel_shelf = Shelf.objects.all().get(shelf_id='98') #This is the Italian shelf in the Ready Meals aisle
            a = getProductInfoByShelf(sel_shelf, shopper)
     
    shelf_id_list = [83, 124, 177]
    #, 186, 304, 310, 319
    for id in shelf_id_list:
        sel_shelf = Shelf.objects.all().get(shelf_id=id)
        b = getProductInfoByShelf(sel_shelf, shopper)
        
    return sel_shelf
        
        
def getProductInfoByShelf(shelf, shopper):
      
   
    temp_product_list = []      
    #going to use this to hold our products whilst we go and fetch extra info
    
    ## get basic product info
    json_products_file = urlopen('http://www.techfortesco.com/groceryapi_b1/restservice.aspx?command=LISTPRODUCTSBYCATEGORY&category='+ \
                                  shelf.shelf_id.__str__() +'&sessionkey='+ shopper.curr_sess_key + '&EXTENDEDINFO=N')
    
    products_dict = simplejson.loads(json_products_file.read())
    for TopLevelNode, TopValue in products_dict.iteritems():
        # at top level, have some elements, ...
        if (TopLevelNode=='Products'):         #TODO - is this a robust way to do this?
            JListOfProducts = TopValue
            for J_Product in JListOfProducts:
                #J_Product is a dict
                for Key, Value in J_Product.iteritems():
                    if (Key=='ProductId'):
                        temp_id = Value
                    elif (Key=='Name'):
                        temp_name = Value
                    elif (Key=='ImagePath'):
                        temp_img_path = Value
                    elif (Key=='Price'):
                        temp_price = Value
    
                product = Product( name=temp_name , prod_id=temp_id , image_url=temp_img_path , price=temp_price , storage_info='')
                product.save()
                product.shelves.add(shelf)
                temp_product_list.append(product)
   
   
    ##get extended product info - one at a time
    #NB could do this somewhere else in the program, for faster response, but would then need to save temp_product list to database here
    for product in temp_product_list:  
        product.save()
        try:
            retrieveProductExtendedDetails(product, shopper)
        #except(ValueError):
        #    continue
        finally:
            product.save()
    return shelf
        
        
def retrieveProductExtendedDetails(product, shopper):
    #gets them from the Tesco API, and saves the resulting object to the database
    #get the extended product info using the id as a product 
    
    # TODO - validation on every call that requires the returned document to be in a specific format
    r_grams = re.compile(r'[0-9\.]+(?=G)')
    r_sample_amount = re.compile(r'[0-9\.]+(?=g)')
    r_calories = re.compile(r'[0-9\.]+(?=kcal)')
    try:
        product_grams = re.findall(r_grams, product.name)[0]
    except(IndexError):
        return product
    else:
        product.product_weight_grams = product_grams
            
        json_oneprod_file = urlopen('http://www.techfortesco.com/groceryapi_b1/restservice.aspx?command=PRODUCTSEARCH&searchtext='+ \
                                  product.prod_id.__str__() +'&sessionkey='+ shopper.curr_sess_key.__str__() + '&EXTENDEDINFO=Y')
        #parse the returned JSON containing the extended product details
        oneprod_dict = simplejson.loads(json_oneprod_file.read())
        for TopLevelNode, TopValue in oneprod_dict.iteritems():
            #at top level, have StatusCode, StatusInfo, PageNumber, TotalPageCount, TotalProductCount, PageProductCount, Products
     
            if (TopLevelNode=='Products'):         #TODO - is this a robust way to do this?
                # department_dict = simplejson.loads(Value)
                try:
                    product_info_dict = TopValue[0]
                except(IndexError):
                    product.save()
                    return product
                #we should only ever have one search result - ie only one product - so can use only the list 0th index
                #TODO - need to validate that there is (at least) one result returned
                for Key, Value in product_info_dict.iteritems():
                    if (Key=='StorageInfo'):
                        product.storage_info = Value
                    #TODO - going to be storing more product details here!!
                    #dont use rda values - theyre linked to serving size which is not always easy to parse
                    #if (Key=='RDA_Calories_Count'):
                     #   product.calories = Value
                        #incorrect!! this will give the amount of calories in a set amount indicated
                        #this set amount is not, in general, equivalent to the amount in the product 
                        #TODO!!
                    #if (Key=='RDA_Sugar_Grammes'):
                    #    product.sugar_grams = Value
                    #if (Key=='RDA_Saturates_Grammes'):
                    #    product.sat_fat_grams = Value
                    
                    if (Key=='Nutrients'):
                        # if this is the key, the value is a list of dictionaries
                        # where each dictionary holds the information associated with each nutrient
                        
                        nutr_dict_list = Value
                        desired_nutr_info = {'Sugars' : product.sugar_grams, 'Saturates' : product.sat_fat_grams, \
                                                     'Fibre' : product.fibre_grams, '*Salt Equivalent' : product.salt_grams }
                        for nutrient_dictionary in nutr_dict_list:
                            sample_amount_grams = 0
                            nutrient_name = ""
                            for Key2, Value2 in nutrient_dictionary.iteritems():
                                if (Key2=='NutrientName'):
                                    nutrient_name = Value2
                                    
                                    
                                if (Key2=='SampleDescription'):
                                    try:
                                        sample_amount_grams = re.findall(r_sample_amount, Value2)[0]
                                    except(IndexError):
                                        continue
                                    
                            for Key2, Value2 in nutrient_dictionary.iteritems():     
                                #exclude energy from dictionary because need to parse it differently
                                if (Key2=='SampleSize'):
                                    if (nutrient_name=='Energy'):
                                        #need to parse 'Value' actually. TODO
                                        try:
                                            sample_calories = re.findall(r_calories, Value2)[0]
                                        except(IndexError):
                                            continue
                                        else:
                                            if (float(sample_amount_grams)!=0):
                                                calories = float(sample_calories)*float(product_grams)/float(sample_amount_grams)
                                                product.calories = int(calories)
                                    
                                        #if (nutrient_name=='Sugars' or nutrient_name=='Saturates' or \
                                         #   nutrient_name=='Fibre' or nutrient_name=='*Salt Equivalent'):
                                    try:
                                        nutr_grams = re.findall(r_sample_amount, Value2)[0]
                                    except(IndexError):
                                        continue
                                    else:
                                        if (float(sample_amount_grams)!=0):
                                            if (nutrient_name=='Sugars'):
                                                product.sugar_grams = float(nutr_grams)*float(product_grams)/float(sample_amount_grams)
                                            if (nutrient_name=='Saturates' or nutrient_name=='of which saturates'):
                                                    product.sat_fat_grams = float(nutr_grams)*float(product_grams)/float(sample_amount_grams)
                                            if (nutrient_name=='Fibre'):
                                                    product.fibre_grams = float(nutr_grams)*float(product_grams)/float(sample_amount_grams)
                                            if (nutrient_name=='*Salt Equivalent'):
                                                    product.salt_grams = float(nutr_grams)*float(product_grams)/float(sample_amount_grams)
                                            # i hope that Value is a pointer... TODO -test
                                        
                            
                            #TODO - multiply nutrient values calculated so far by (product_grams/sample_amount_grams)
    
        product.save()
        return product
    #not necessary?? but we can now manipulate the product where this function is called
        
        
def calcProductHealthRating(product):
    #use product info retrieved from tesco API to calculate a single health rating for the product
    
    #first calculate the levels of each nutrient per calorie in the product
    sat_fat_percalorie = product.sat_fat_grams / product.calories
    sugar_percalorie = product.sat_fat_grams / product.calories
    salt_percalorie = product.salt_grams / product.calories
        
    #mono_unsat_fat_percalorie = product.mono_unsat_fat_grams / product.calories
    #protein_percalorie = product.protein_grams / product.calories
    
    fibre_percalorie = product.fibre_grams / product.calories
    per_calorie_list = [sat_fat_percalorie, sugar_percalorie, salt_percalorie, fibre_percalorie]
    
    #do the calculation
    health_rating = 0.0
    for position, nutrient_per_calorie in enumerate(per_calorie_list):
        rating_backup = health_rating
        try:
            nutrient_dietary_excess_ratio =  (rda_list[position] - av_amount_list[position]) / rda_list[position]
            #in this implementation you need to ensure the 3 lists have nutrients in the same order
            #if theres normally too much in the diet, the result is negative. If theres normally too little, it is positive
            #ie larger positive values mean the product is healthier
            
            normalised_nutrient_amount = nutrient_per_calorie / rda_list[position]
            #normalise rating contribution. 
            #Dont want the health rating to be dependent on how large the amount of nutrient you eat is
            #want healthiness/unhealthiness to be judged by how much you exceed the recommended amounts
            rating_contribution = nutrient_dietary_excess_ratio * normalised_nutrient_amount
            
            health_impact_factor = 1
            rating_contribution = rating_contribution * health_impact_factor
            #this is still not quite right?
            #maybe want to cap contribution of 'good' foods so that you can't be penalised for eating too much?
            
            health_rating = health_rating + rating_contribution
        except(ValueError):
            #don't have the necessary info to calculate the rating for this product
            health_rating = rating_backup

    product.health_rating = health_rating
    product.save()
    
def calcPricePerCalorie(product):
    price_per_calorie = product.price / product.calories
    product.price_per_calorie = price_per_calorie
    product.save()

        