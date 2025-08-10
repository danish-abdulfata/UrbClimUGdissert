import ee

ee.Authenticate(force=True, auth_mode=gcloud)
ee.Initialize(project='uclgeodissertation')
print(ee.String('Hello from the Earth Engine servers!').getInfo())