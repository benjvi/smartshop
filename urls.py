from django.conf.urls.defaults import patterns, include, url
from SmartShop.shopapp.views import simplePage, tescoLogin, getDetails, getJSON, \
 getProductJSON, updateProductDetails, calculateMetrics, foodStatistics, calculateAllMetrics
# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'SmartShop.views.home', name='home'),
    # url(r'^SmartShop/', include('SmartShop.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    
    ('^hello/$', simplePage),
    ('^tesco/$', tescoLogin),
    ('^details/$', getDetails),
    ('^json/$', getJSON),   
    ('^stats/$', foodStatistics),
    ('^product/(?P<product>\w+)$', getProductJSON),
    ('^update/(?P<product>\w+)$', updateProductDetails),
    ('^calculate/(?P<product_id>\w+)$', calculateMetrics),
    ('^calculateall/$', calculateAllMetrics),
    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
)

