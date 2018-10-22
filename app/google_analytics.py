async def ga_ua_id_processor(request):
    return {'analytics_ua_id': request.app['ANALYTICS_UA_ID']}
