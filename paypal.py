import decimal
import logging
import urllib
import urllib2

from google.appengine.api import urlfetch

# hack to enable urllib to work with Python
import os
os.environ['foo_proxy'] = 'bar'

from django.utils import simplejson as json

import settings
import model
import util

class PayCart( object ):
  def __init__( self, amount, return_url, cancel_url, remote_address, cart, secondary_receiver, purchase,ipn_url=None, shipping2=None):
    headers = {
      'X-PAYPAL-SECURITY-USERID': settings.PAYPAL_USERID, 
      'X-PAYPAL-SECURITY-PASSWORD': settings.PAYPAL_PASSWORD, 
      'X-PAYPAL-SECURITY-SIGNATURE': settings.PAYPAL_SIGNATURE, 
      'X-PAYPAL-REQUEST-DATA-FORMAT': 'JSON',
      'X-PAYPAL-RESPONSE-DATA-FORMAT': 'JSON',
      'X-PAYPAL-APPLICATION-ID': settings.PAYPAL_APPLICATION_ID,
      'X-PAYPAL-DEVICE-IPADDRESS': remote_address,
    }

    data = {
      'currencyCode': 'USD',
      'returnUrl': return_url,
      'cancelUrl': cancel_url,
      'requestEnvelope': { 'errorLanguage': 'en_US' },
      'reverseAllParallelPaymentsOnError' : 'true',
    } 

    if shipping2:
      data['actionType'] = 'CREATE'
    else:
      data['actionType'] = 'CREATE'
	 
    if secondary_receiver == None: # simple payment
      data['receiverList'] = {'receiver':[]}  
      distinctownerlist=[]
      for c in cart:
        try:
          distinctownerlist.remove(c.item.owner)
          distinctownerlist.insert(0,c.item.owner)
        except:
          distinctownerlist.insert(0,c.item.owner)
	    
      for owner in distinctownerlist:
        amount=0.0
        email=util.paypal_email(owner)
        shipping=None
        index=0
        for c in cart:
          if c.item.owner==owner:
            amount=amount+(c.item.price*c.qty)
            shipping=c.shipping
        reciever ={ 'email': email,'amount': '%0.2f' % (amount+shipping.price)}
        data['receiverList']['receiver'].append(reciever)
	
    else: # chained
      commission = amount * settings.PAYPAL_COMMISSION
      data['receiverList'] = {'receiver':[]}  
      distinctownerlist=[]
      for c in cart:
        try:
          distinctownerlist.remove(c.item.owner)
          distinctownerlist.insert(0,c.item.owner)
        except:
          distinctownerlist.insert(0,c.item.owner)
	    
      for owner in distinctownerlist:
        amount=0.0
        email=util.paypal_email(owner)
        shipping=None
        index=0
        for c in cart:
          if c.item.owner==owner:
            amount=amount+(c.item.price*c.qty)
            shipping=c.shipping
        reciever ={ 'email': email,'amount': '%0.2f' % (amount+shipping.price)}
        data['receiverList']['receiver'].append(reciever)

    if ipn_url != None:
      data['ipnNotificationUrl'] = ipn_url

    self.raw_request = json.dumps(data)
    #request = urllib2.Request( "%s%s" % ( settings.PAYPAL_ENDPOINT, "Pay" ), data=self.raw_request, headers=headers )
    #self.raw_response = urllib2.urlopen( request ).read() 
    self.raw_response = url_request( "%s%s" % ( settings.PAYPAL_ENDPOINT, "Pay" ), data=self.raw_request, headers=headers ).content() 
    logging.info( "response was: %s" % self.raw_response )
    self.response = json.loads( self.raw_response )
    if self.raw_response.find("580022")>0:
      return None
    data = {
      'requestEnvelope': { 'detailLevel': 'ReturnAll','errorLanguage': 'en_US' },
      'payKey': self.paykey(),
      'senderOptions': {},
    } 
    # 'senderOptions': { 'requireShippingAddressSelection': 'true', 'shareAddress': 'true' },
    distinctownerlist=[]
    for c in cart:
      try:
        distinctownerlist.remove(c.item.owner)
        distinctownerlist.insert(0,c.item.owner)
      except:
        distinctownerlist.insert(0,c.item.owner)
    
    index=0
    itemindex=0
    payownerdata=[]
    for owner in distinctownerlist:
      recieverdata={'reciever':{'email': util.paypal_email(owner)},'description': 'Lista de articulos del proveedor:%s'%(util.paypal_email(owner)),'invoiceData':{'item':[]}}
      itemqtytotal=0
      shipping=None
      for c in cart:
        itemqtytotal=itemqtytotal+c.qty
        if c.item.owner==owner:
          item={'name': '%s'%(c.item.title),'itemCount': '%s'%(c.qty),'itemPrice': '%0.2f'%(c.item.price),'price': '%0.2f'%(c.item.price*c.qty)}
          recieverdata['invoiceData']['item'].insert(itemindex,item)
          shipping=c.shipping
          if itemindex==0:
            recieverdata['invoiceData']['totalShipping']='%0.2f'%(shipping.price)      
          itemindex=itemindex+1
      payownerdata.insert(index,recieverdata)
      itemindex=0
      index=index+1
    data['recieverOptions']=payownerdata
    logging.info( json.dumps(data) )
    options_raw_response = url_request( "%s%s" % ( settings.PAYPAL_ENDPOINT, "SetPaymentOptions" ), data=json.dumps(data), headers=headers ).content() 
    logging.info( 'SetPaymentOptions response: %s' % options_raw_response )
	
    if shipping2:
      # generate setpaymentoptions request
      options_raw_request = json.dumps( { 
        'payKey': self.paykey(),
        'senderOptions': { 'requireShippingAddressSelection': 'true', 'shareAddress': 'true' },
        'requestEnvelope': { 'errorLanguage': 'en_US' }
      } )
      options_raw_response = url_request( "%s%s" % ( settings.PAYPAL_ENDPOINT, "SetPaymentOptions" ), data=options_raw_request, headers=headers ).content() 
      logging.info( 'SetPaymentOptions response: %s' % options_raw_response )
      # TODO check response was OK
    
  def status( self ):
    if self.response.has_key( 'paymentExecStatus' ):
      return self.response['paymentExecStatus']
    else:
      return None 

  def amount( self ):
    return decimal.Decimal(self.results[ 'payment_gross' ])

  def paykey( self ):
    return self.response['payKey']

  def next_url( self ):
    return '%s?cmd=_ap-payment&paykey=%s' % ( settings.PAYPAL_PAYMENT_HOST, self.response['payKey'] )

class IPN( object ):
  def __init__( self, request ):
    # verify that the request is paypal's
    self.error = None
    #verify_request = urllib2.Request( "%s?cmd=_notify-validate" % settings.PAYPAL_PAYMENT_HOST, data=urllib.urlencode( request.POST.copy() ) )
    #verify_response = urllib2.urlopen( verify_request )
    verify_response = url_request( "%s?cmd=_notify-validate" % settings.PAYPAL_PAYMENT_HOST, data=urllib.urlencode( request.POST.copy() ) )
    # check code
    if verify_response.code() != 200:
      self.error = 'EL codigo de respuesta PayPal fue %i' % verify_response.code()
      return
    # check response
    raw_response = verify_response.content()
    if raw_response != 'VERIFIED':
      self.error = 'La respuesta de PayPal fue "%s"' % raw_response
      return
    # check payment status
    if request.get('status') != 'COMPLETED':
      self.error = 'El estatus de PayPal fue "%s"' % request.get('status')
      return

    (currency, amount) = request.get( "transaction[0].amount" ).split(' ')
    if currency != 'USD':
      self.error = 'Divisa Incorrecta %s' % currency
      return

    self.amount = decimal.Decimal(amount)

  def success( self ):
    return self.error == None

class Pay( object ):
  def __init__( self, amount, return_url, cancel_url, remote_address, primary_receiver, secondary_receiver, purchase,ipn_url=None, shipping2=None):
    headers = {
      'X-PAYPAL-SECURITY-USERID': settings.PAYPAL_USERID, 
      'X-PAYPAL-SECURITY-PASSWORD': settings.PAYPAL_PASSWORD, 
      'X-PAYPAL-SECURITY-SIGNATURE': settings.PAYPAL_SIGNATURE, 
      'X-PAYPAL-REQUEST-DATA-FORMAT': 'JSON',
      'X-PAYPAL-RESPONSE-DATA-FORMAT': 'JSON',
      'X-PAYPAL-APPLICATION-ID': settings.PAYPAL_APPLICATION_ID,
      'X-PAYPAL-DEVICE-IPADDRESS': remote_address,
    }

    data = {
      'currencyCode': 'USD',
      'returnUrl': return_url,
      'cancelUrl': cancel_url,
      'requestEnvelope': { 'errorLanguage': 'en_US' },
      'reverseAllParallelPaymentsOnError' : 'true',
    } 

    if shipping2:
      data['actionType'] = 'CREATE'
    else:
      data['actionType'] = 'CREATE'

    if secondary_receiver == None: # simple payment
      data['receiverList'] = { 'receiver': [ { 'email': primary_receiver, 'amount': '%f' % amount } ] }
    else: # chained
      commission = amount * settings.PAYPAL_COMMISSION
      data['receiverList'] = { 'receiver': [{ 'email': primary_receiver,'amount': '%0.2f' % (amount+purchase.shipping.price)}]}

    if ipn_url != None:
      data['ipnNotificationUrl'] = ipn_url

    self.raw_request = json.dumps(data)
    #request = urllib2.Request( "%s%s" % ( settings.PAYPAL_ENDPOINT, "Pay" ), data=self.raw_request, headers=headers )
    #self.raw_response = urllib2.urlopen( request ).read() 
    self.raw_response = url_request( "%s%s" % ( settings.PAYPAL_ENDPOINT, "Pay" ), data=self.raw_request, headers=headers ).content() 
    logging.info( "response was: %s" % self.raw_response )
    self.response = json.loads( self.raw_response )
    if self.raw_response.find("580022")>0:
      return None
    data = {
      'requestEnvelope': { 'detailLevel': 'ReturnAll','errorLanguage': 'en_US' },
      'payKey': self.paykey(),
      'senderOptions': {},
    } 
    payownerdata=[]
    recieverdata={'reciever':{'email': util.paypal_email(purchase.item.owner)},'description': 'Lista de articulos del proveedor:%s'%(util.paypal_email(purchase.item.owner)),'invoiceData':{'item':[{'name': '%s'%(purchase.item.title),'itemCount': '%s'%(purchase.qty),'itemPrice': '%0.2f'%(purchase.item.price),'price': '%0.2f'%(purchase.item.price*purchase.qty)}],'totalShipping':'%0.2f'%(purchase.shipping.price)}}
    payownerdata.insert(0,recieverdata)
    data['recieverOptions']=payownerdata
    logging.info( json.dumps(data) )
    options_raw_response = url_request( "%s%s" % ( settings.PAYPAL_ENDPOINT, "SetPaymentOptions" ), data=json.dumps(data), headers=headers ).content() 
    logging.info( 'SetPaymentOptions response: %s' % options_raw_response )
	
    if shipping2:
      # generate setpaymentoptions request
      options_raw_request = json.dumps( { 
        'payKey': self.paykey(),
        'senderOptions': { 'requireShippingAddressSelection': 'true', 'shareAddress': 'true' },
        'requestEnvelope': { 'errorLanguage': 'en_US' }
      } )
      options_raw_response = url_request( "%s%s" % ( settings.PAYPAL_ENDPOINT, "SetPaymentOptions" ), data=options_raw_request, headers=headers ).content() 
      logging.info( 'SetPaymentOptions response: %s' % options_raw_response )
      # TODO check response was OK
    
  def status( self ):
    if self.response.has_key( 'paymentExecStatus' ):
      return self.response['paymentExecStatus']
    else:
      return None 

  def amount( self ):
    return decimal.Decimal(self.results[ 'payment_gross' ])

  def paykey( self ):
    return self.response['payKey']

  def next_url( self ):
    return '%s?cmd=_ap-payment&paykey=%s' % ( settings.PAYPAL_PAYMENT_HOST, self.response['payKey'] )

class IPN( object ):
  def __init__( self, request ):
    # verify that the request is paypal's
    self.error = None
    #verify_request = urllib2.Request( "%s?cmd=_notify-validate" % settings.PAYPAL_PAYMENT_HOST, data=urllib.urlencode( request.POST.copy() ) )
    #verify_response = urllib2.urlopen( verify_request )
    verify_response = url_request( "%s?cmd=_notify-validate" % settings.PAYPAL_PAYMENT_HOST, data=urllib.urlencode( request.POST.copy() ) )
    # check code
    if verify_response.code() != 200:
      self.error = 'EL codigo de respuesta PayPal fue %i' % verify_response.code()
      return
    # check response
    raw_response = verify_response.content()
    if raw_response != 'VERIFIED':
      self.error = 'La respuesta de PayPal fue "%s"' % raw_response
      return
    # check payment status
    if request.get('status') != 'COMPLETED':
      self.error = 'El estatus de PayPal fue "%s"' % request.get('status')
      return

    (currency, amount) = request.get( "transaction[0].amount" ).split(' ')
    if currency != 'USD':
      self.error = 'Divisa Incorrecta %s' % currency
      return

    self.amount = decimal.Decimal(amount)

  def success( self ):
    return self.error == None

class ShippingAddress( object ):
  def __init__( self, paykey, remote_address ):
    headers = {
      'X-PAYPAL-SECURITY-USERID': settings.PAYPAL_USERID, 
      'X-PAYPAL-SECURITY-PASSWORD': settings.PAYPAL_PASSWORD, 
      'X-PAYPAL-SECURITY-SIGNATURE': settings.PAYPAL_SIGNATURE, 
      'X-PAYPAL-REQUEST-DATA-FORMAT': 'JSON',
      'X-PAYPAL-RESPONSE-DATA-FORMAT': 'JSON',
      'X-PAYPAL-APPLICATION-ID': settings.PAYPAL_APPLICATION_ID,
      'X-PAYPAL-DEVICE-IPADDRESS': remote_address,
    }

    data = {
      'key': paykey,
      'requestEnvelope': { 'errorLanguage': 'en_US' },
    } 

    self.raw_request = json.dumps(data)
    self.raw_response = url_request( "%s%s" % ( settings.PAYPAL_ENDPOINT, "GetShippingAddresses" ), data=self.raw_request, headers=headers ).content() 
    logging.info( "response was: %s" % self.raw_response )
    self.response = json.loads( self.raw_response )

class url_request( object ): 
  '''wrapper for urlfetch'''
  def __init__( self, url, data=None, headers={} ):
    # urlfetch - validated
    self.response = urlfetch.fetch( url, payload=data, headers=headers, method=urlfetch.POST, validate_certificate=True )
    # urllib - not validated
    # request = urllib2.Request(url, data=data, headers=headers) 
    # self.response = urllib2.urlopen( request )

  def content( self ):
    return self.response.content

  def code( self ):
    return self.response.status_code
