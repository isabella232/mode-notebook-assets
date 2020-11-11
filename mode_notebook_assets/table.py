import json

from IPython.core.display import display, HTML

class AgGridTable(object):
    """
        Parameters
        ----------
        df : Pandas DataFrame
        div_id : Name of your div element uniquely identify this ag-grid object

        Returns
        -------
        HTML string

        Notes
        ------

        ag = AgGridTable(df, div_id="your_div_name_no_dashes")
        ag.show()


        For the URLs to work, you'll need to ensure you encode them correctly. For simple URLs
        it probably won't be an issue but for more complex URLs with a query there's some finessing required.
        Here's a more complex case:
        "https://app.us1.signalfx.com/#/apm/traces?"+\
            urllib.parse.urlencode(query=url_query, safe="[]=:").replace("%27", "%22")
    """

    UNQUOTE_FUNCTIONS = ['dateFormatter', 'urlFormatter']
    
    def __init__(self, df, div_id=""):
        self.div_id = div_id
        self.header = """
          <script src="https://unpkg.com/ag-grid-community/dist/ag-grid-community.min.noStyle.js"></script>
          <link rel="stylesheet" href="https://unpkg.com/ag-grid-community/dist/styles/ag-grid.css">
          <link rel="stylesheet" href="https://unpkg.com/ag-grid-community/dist/styles/ag-theme-balham.css">
          """

        # set the column headers
        self.column_defs = self.dataframe_dtypes_to_column_definitions(df)
        self.column_defs_json = json.dumps(self.column_defs)
        self.column_defs_json = self.unquote_function_names(self.column_defs_json, self.UNQUOTE_FUNCTIONS)

        self.body = '''<div id="{div_id}" style="height: 600px;width:100%;" class="ag-theme-balham"></div>
  
            <script type="text/javascript" charset="utf-8">
            
              function onBtnExportDataAsCsv(div_name) {{
                  window['gridOptions_'+div_name].api.exportDataAsCsv();
              }}
              
              function dateFormatter(params) {{
                          if (params.value == null) return '';
                  if (params.value == 'NaT') return '';
                  return new Date(params.value).toISOString();
              }}

              function urlFormatter(params) {{
                  if (params.value == null) return '';
                  return '<a href="'+ params.value + '" target="_blank">'+ params.value+'</a>'
              }}
              
              // specify the columns
              var columnDefs = {column_defs};
  
              // specify the data
              var rowData = {data};
  
              // let the grid know which columns and what data to use
              var gridOptions_{div_id} = {{
                columnDefs: columnDefs,
                rowData: rowData,
                pagination: true
              }};
  
            // lookup the container we want the Grid to use
            var eGridDiv = document.querySelector('#{div_id}');
  
            // create the grid passing in the div to use together with the columns & data we want to use
            new agGrid.Grid(eGridDiv, gridOptions_{div_id});
  
            </script>
        '''.format(
            div_id=self.div_id,
            column_defs=self.column_defs_json,
            data=df.to_json(orient='records'),
        )

        self.csv_export_button = '''<div id="csvExportbutton_{div_id}" style="margin: 10px 0">
          <button onclick="onBtnExportDataAsCsv('{div_id}')">Export CSV</button>
        </div>
        '''.format(div_id=div_id)

        self.html = "<html>" + self.header + self.body + self.csv_export_button + "</html>"

    def unquote_function_names(self, json_str, funcs):
      for f in funcs:
        json_str = json_str.replace('"{}"'.format(f), "{}".format(f))
      return json_str

    def dataframe_dtypes_to_column_definitions(self, df) -> list:
        """
        """
        colDefs = []
        for col, dtype in df.dtypes.iteritems():
            colDef = {"headerName": col, "field": col, "sortable": True, "filter": True, "editable": True,
                    "resizable": True, "filterParams": {"applyButton": True, "resetButton": True}}
            if any(s in str(dtype) for s in ('int', 'float')):
                colDef["filter"] = 'agNumberColumnFilter'
            elif 'date' in str(dtype):
                colDef["filter"] = 'agDateColumnFilter'
                colDef["valueFormatter"] = 'dateFormatter'

            # sensible defaults, if the column is a URL, assign urlFormatter for its cell rendering
            if 'url' in col:
              colDef["cellRenderer"] = 'urlFormatter'
            colDefs.append(colDef)

            colDefs.append(colDef)

        return colDefs

    def show(self):
        display(HTML(self.header + self.body + self.csv_export_button))
