import ee

ee.Authenticate()
ee.Initialize(project='uclgeodissertation')
print(ee.String('Hello from the Earth Engine servers!').getInfo())