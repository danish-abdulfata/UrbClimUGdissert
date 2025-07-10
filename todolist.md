# To Do List

### Questions/Research Needed
Just to take note of pending tasks and potential further research needed.

- Repository cleanup, removal of unsused files and scripts.
 - ongoing, and will probably lead to a lot of the example scripts being deleted

- UHI vs UHI effect, clarify terminology.



# Supervision questions
- updated UCL Geography disseration coversheet
- Preface section?


#### Model Questions
- The lon lat coordinate mismatch
		1. possible mismatch at the graphing level when unflattening the data
			- will need to round up lat/lon values, 4-6dp
		 - another way is to extract a dataarray with just timestamp data, and re-apply meshgrid through .expand_dims
				- only will work IF data is originally sorted by monotonically increasing longitude coords.
		2. at the model level where I misinterpret how the modelled data is output
	 3. not the same but Will need to cleanup the high dp lat/lon, and ensure that grid coordinates are consistent with eachother.


- split processing to individual variables?

- Hilly urban areas? How does topography affect calculations in SUEWS.
- bulk surface temperature vs skin temperature?

- 2 scenarios
	- normal LCZ determined cover fractions
	- modified surface cover fractions for urban heat mitigation
 
- which rural site shoud i compare? should i run a modelled counterfactual instead? 
- 	- For testing:
		- graphs showing peak T2 over a day
		- Water and Energy fluxes?
			- anthroprogenic heat influences?
			- variables for wet bulb calculations? (air temp, wind, rel humidity)

#### Dissertation Writing

- What sort of figures?
	- Summary statistics (table or graph?)
	- Site Area outline, elevation and satellite?, LCZ covers.
	- 
- equations, include SUEWS figures.

- background of site of study can be written now


### Good example dissertations

- [Hydrological modelling under different climate change scenarios](https://liveuclac.sharepoint.com/:b:/r/sites/Geography/MapLibrary/UG%20Dissertations/2016_BCDE7_Modelling%20the%20impacts%20of%20climate%20change%20on%20flooding%20in%20the%20river%20Parrett%20basin%20Somerset.pdf?csf=1&web=1&e=kwVHDb)

- [Dengue modelling scioeconomic](https://liveuclac.sharepoint.com/:b:/r/sites/Geography/MapLibrary/UG%20Dissertations/2021_MQCW7_INFLUENCE%20OF%20SOCIOECONOMIC%20FACTORS%20ON%20THE%20FUTURE%20SPATIOTEMPORAL%20PROLIFERATION%20OF%20DENGUE%20FEVER.pdf?csf=1&web=1&e=aueic5)

- [Projections of thermally induced coral bleaching](https://liveuclac.sharepoint.com/sites/Geography/MapLibrary/UG%20Dissertations/Forms/AllItems.aspx?id=%2Fsites%2FGeography%2FMapLibrary%2FUG%20Dissertations%2F2022%5FFVLG6%5F%20Projections%20of%20thermally%20induced%20coral%20bleaching%2Epdf&q=chris%20brierley&parent=%2Fsites%2FGeography%2FMapLibrary%2FUG%20Dissertations&parentview=7)

### Other

