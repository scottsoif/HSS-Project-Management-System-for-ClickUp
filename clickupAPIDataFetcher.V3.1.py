# -*- coding: utf-8 -*-
"""
Created on  June 2019

@author: Scott A. Soifer
"""

import datetime
import requests
from collections import defaultdict
import dash
import dash_table
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd


# ID's for each clickUp 'space'
spaceids = ['1330671', '1302931','1320346', '1325739']  # 1302931 == research

tags = set([]) # list of all tags found
tags2 = [] # used for dash drops menu
projects = defaultdict(list) # { id: [project name , [tags] ]}

# used for picking a current project status or deadline
stages = ["Collect Materials" , "Collect Data", "Analyze Data", "Manuscript Under Review" ]
# contains project Id's at current stages --> {stage: [list of proj Id's] }
stages2 = defaultdict(list) 

# Authentication key and URL to access clickUp API
headers = { 'Authorization': '***API Key Removed***' }   
url = 'https://api.clickup.com/api/v1/team/1241606/task'
# this is for getting the project names and respective id's
urlProj = 'https://api.clickup.com/api/v1/space/1302931/project'

# stores all information from API request
r = requests.get(url, headers=headers)
r2 = requests.get(urlProj, headers=headers)
print("Status code =  " , r, "\n")
print("Status code =  " , r2, "\n")
r = r.json()["tasks"] # variable holding all data pulled from clickUp
r2 = r2.json()["projects"][1]["lists"] # contain project name and id data


def saveToFile(): # saves json file to directory of this python file
    time = "dataExport " +str(datetime.datetime.now().strftime("%m/%d/%Y-%H:%M:%S")) + '.txt'
    f = open(time , 'a')
    f.write(str(r))
    f.close()

def inProgress( element ):  # gets all the active projects
    if "in progress" == element["status"]["status"]:
        return element["name"]
       
        
def collectStageItem( element , stage ): # identifies all projects in 
                                 # at specific stage
    if inProgress( element ) and stage in element["name"]:
        return element
    
# =============================================================================
#  1. a specifc tag and stage are passed in ex: compTag('arjr', 'Collect Data')  
#  2. if a project is at the stage and contain the tag it will be added to the table
#  3. stages2 contains the stages as key and the project id's are one of the item stored
#  4. the structure for stages2 = { id, [ [list proj id's] , time deadline ] }
# =============================================================================
def compTag(tag, stage ):
    print("All projects with status '", stage , "' and 'tag'=" , tag, "\n\n")
    for i in stages2[stage]:
        if tag in projects[i[0]][1]:
            ##  note i[1][:-3]  3 zeros are removed below for program to work
            ## there is some glitch in system
            time = datetime.datetime.fromtimestamp(int(i[1][:-3])).strftime("%a, %B %d %Y")
            print("Project ID: ", i[0])
            print("Project Name: ", projects[i[0]][0])
            print("Project Due Date: " , time )
            print("*** ")
            tableInfo.add((i[0], projects[i[0]][0], time )) # table used for dash output
    
    
def getProjID( element ): 
    return element["list"]["id"]


def main():
    for i in r2:  # adds the id and proj name to list
                  # the proj tags will get added a few lines below
        projects[i["id"]].append( i["name"] )
        
    for i in r:
        tempProjTags = []
        for j in i["tags"]:
            # all the tags are added to a master set
            # a set is used to prevent duplicate tags in list
            tags.add(j["name"])
            # used to prepare addition of tags to projects dict.
            tempProjTags.append(j["name"]) 
        if tempProjTags: # removes the tags with no content
            # adds tags to projects list, see comment a few lines above
            projects[getProjID(i)].append(tempProjTags) 
            
        for j in stages: # used to connect stages with project ids
            if collectStageItem(i, j):
                stages2[j].append( [getProjID(i), i["due_date"] ] )
    for i in sorted(tags):  # used for dash dropdown menu    
        tags2.append({'label': i , 'value': i } )
    for i in projects: # print to console to see all available projects
        print(projects[i])


# =============================================================================
#  ****     Dash Code  ---  Dash Code  ---  Dash Code  ---  Dash Code     ****      
# =============================================================================   
tableInfo = set([])
df = pd.DataFrame(list(tableInfo), columns = ['Proj id', 'ProjName', 'Due Date'])

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
    
app.layout = html.Div([
    html.H4(children='ClickUp Data Export (2019)'),
    
    html.Div(id='output-container-button'),
    html.Div([
    dcc.Dropdown(
    id = 'dropDown',
    options=  tags2,
    multi = True
    ), 
    ] , style = {'width': '50%'} ),     
        html.Div([    
    dcc.RadioItems(
    id = 'radioItems' ,
    
   options = [ {"label": i, "value": i} for i in stages ]
    
#    options=[
#        
#        {'label': 'Collect Data', 'value': 'Collect Data'},
#        {'label': 'Collect Materials', 'value': 'Collect Materials' },
#    ],
    
    ), 
    html.Button('Submit', id='submit'),
    ] ,style={'columnCount': 2, 'width':'50%' , 'padding-top': 5,  }),
            
    html.Div([
    dash_table.DataTable(
    id='datatable',
    columns=[ {"name": i, "id":i,  "due_date":i} for i in df.columns ],
     data=df.to_dict('records'),
     style_cell={'textAlign': 'center'},
     )] , style={'width':'65%'}
)      
      
    
    
] ,  style={'padding-left': 10})

@app.callback(
    [dash.dependencies.Output('datatable', 'data'),
     dash.dependencies.Output('datatable', 'columns')],
    [dash.dependencies.Input('submit', 'n_clicks')],
    [dash.dependencies.State('dropDown', 'value'),
    dash.dependencies.State('radioItems', 'value')])
def update_output(click, tag, stage):
    tableInfo.clear()
    if( not(click==None or tag==None or stage==None ) ):
        for i in tag:
            compTag( i , stage)
    df = pd.DataFrame(list(tableInfo), columns = ['Proj id', 'ProjName', 'Due Date'])
    return df.to_dict('records'), [ {"name": i, "id": i, "due_date":i} for i in df.columns ]

    


if __name__ == "__main__":
    main()
    app.run_server(debug = False)
 