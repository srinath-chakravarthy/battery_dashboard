# TODO List 
# Cycle Selector Tab
## Featurs to add 
- [ ] Implement Select all cells in the filter/selection button 
- [ ] Implement Clear all selections in the filter/selection button 
- [ ] Implement summary stats for selected cells. Should this be on a Card. What will look nice
- [ ] Modify Load cycle data to be active only if there are selected cells in the list 
  - [ ] Add status indicator for Redash query 
  - [ ] Add confirmation panel if number of cells > 100

# Cycle Plots Tab
## Features to add 
- [ ] Move to hvplot + bokeh for default backend and other rendering engines if needed. 
- [ ] Implement adding 2nd axis to plot 
- [ ] Implement default axis lines and axis ticks for all X-Y plots
- [ ] All custom Plot settings on the Right Hand side as a Card
- [ ] Series settings should be smaller since there might be quite a few series 
  - [ ] Redash type series settings is better i think, rather than this way. Present a table and let the user change it 
    -  [ ] If num series > 10 do not give the ability to change
- [ ] Global marker for marker/line settings and color

# Database level settings. 
- [ ] Definitely add status marker for if test is complete or not
      I think it can be at the query level. 
- [ ] Automate File handling for each cell
- [ ] Common database for FEST and Solstics - perhaps with a cell_type in the cell
  - [ ] Need to coordinate nominal capacity and perhaps make querying faster. 
  - [ ] How to handle electrolyte type and code here ? 

# ML level page / tab
- [ ] Introductory data analytics and analysis tab
- [ ] Testing based clustering and filtering 
- [ ] Testing based analytics 