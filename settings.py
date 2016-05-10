# settings for app
# PAYPAL_ENDPOINT = 'https://svcs.sandbox.paypal.com/AdaptivePayments/' # sandbox
PAYPAL_ENDPOINT = 'https://svcs.paypal.com/AdaptivePayments/' # production
# PAYPAL_PAYMENT_HOST = 'https://www.sandbox.paypal.com/us/cgi-bin/webscr' # sandbox
PAYPAL_PAYMENT_HOST = 'https://www.paypal.com/webscr' # production

#live mex
PAYPAL_USERID = 'llucio_api1.hotmail.com'
PAYPAL_PASSWORD = 'DBGCH9FNDTYV55ED'
PAYPAL_SIGNATURE = 'AUXFycMr2vpIScLhrCTGgAqYVKnKAN67H0MJqtIPzP4N8zi0NbtwzU6j'
PAYPAL_APPLICATION_ID = 'APP-95Y84419JB753840B'
PAYPAL_EMAIL = 'llucio@hotmail.com'

#live usa
#PAYPAL_USERID = 'ppagos8_api1.gmail.com'
#PAYPAL_PASSWORD = 'BK5Y79LDQ8ADWVKJ'
#PAYPAL_SIGNATURE = 'AFcWxV21C7fd0v3bYYYRCpSSRl31Am0ZoOTHsQdBUTx4e4mlGHTMeVvZ'
#PAYPAL_EMAIL = 'ppagos8@gmail.com'


#sandbox mex
# PAYPAL_USERID = 'llucio-facilitator-1_api1.hotmail.com'
# PAYPAL_PASSWORD = '3LKC3FGTXCVFXYHT'
# PAYPAL_SIGNATURE = 'A5jDm2ipcZYaYuQlD4o4v0M6uV0dAnYP3pxYCTJzztfVWp5UXyHmzAm4'
# PAYPAL_APPLICATION_ID = 'APP-80W284485P519543T' # sandbox only
# PAYPAL_EMAIL = 'llucio-facilitator-1@hotmail.com'	
#sandbox usa
# PAYPAL_USERID = 'ppagos8-facilitator-1_api1.gmail.com'
# PAYPAL_PASSWORD = 'H6ZHPUVKJTMNC7GC'
# PAYPAL_SIGNATURE = 'AFcWxV21C7fd0v3bYYYRCpSSRl31A.D9fcgyW8akEaOUjMy-W6Pxw7Ek'
# PAYPAL_APPLICATION_ID = 'APP-80W284485P519543T' # sandbox only
# PAYPAL_EMAIL = 'ppagos8-facilitator-1@gmail.com'

PAYPAL_COMMISSION = 0.05 # 20%

USE_CHAIN = True
#este seria el cliente elq recibe la moyria del pago yel responsable de los reembolsos
# PRIMARY_RECIEVER='llucio@hotmail.com'
# SECONDARY_RECIEVER = 'llucio-facilitator-2@hotmail.com'
USE_IPN = False
USE_EMBEDDED = False
SHIPPING = False # not yet working properly; PayPal bug

EMBEDDED_ENDPOINT = 'https://paypal.com/webapps/adaptivepayment/flow/pay'
# EMBEDDED_ENDPOINT = 'https://www.sandbox.paypal.com/webapps/adaptivepayment/flow/pay'

MAXIMAGENUMBER = 15
MAXIMAGEX = 400
MAXIMAGEY = 400
