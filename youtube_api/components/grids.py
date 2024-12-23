import dash_ag_grid as dag
from dash import html

def youtube_content_grid(data=None):
    """
    Create AG Grid component for youtube video contents records
    """
    if not data:
        return html.Div([
            html.Strong(
                html.P("Please input keyword and click search button for display content list")
            )
        ], className="text-center")

    content_columnDefs = [
        {
            "headerName": "No.",
            "headerClass": "text-center",
            "valueGetter": {"function": "params.node.rowIndex + 1"},
            "width": 70
        },
        {
            "headerName": "Content Image",
            "field": "thumbnail",
            "width": 120,
            "headerClass": "text-center",
            "sortable": False,
            "cellRenderer": "VideoImageRenderer"
        },
        {
            "headerName": "Country",
            "field": "country",
            "width": 100,
            "headerClass": "text-center",
            "unSortIcon": True,
            "cellRenderer": "CountyFlagRenderer"
        },
        {
            "headerName": "Video Title",
            "field": "video",
            "headerClass": "text-center",
            "wrapText": True,
            "unSortIcon": True,
            "cellRenderer": "VideoIdRenderer"
        },
        {
            "headerName": "Channel Title",
            "field": "channel",
            "headerClass": "text-center",
            "unSortIcon": True,
            "cellRenderer": "ChannelIdRenderer"
        },
        {
            "headerName": 'Published At',
            "field": "published_at",
            "width": 120,
            "headerClass": "text-center",
            "unSortIcon": True,
            "cellStyle": {'textAlign': 'center'}
            # "valueGetter": {"function": date_obj},
            # "valueFormatter": {"function": f"d3.timeFormat('%Y/%m/%d')({date_obj})"}
        },
        {
            "headerName": "Statistics",
            'headerClass': 'center-aligned-group-header',
            "children": [
                {
                    "headerName": "View Count",
                    "field": "view_count",
                    "width": 120,
                    "headerClass": "text-center",
                    "unSortIcon": True,
                    "sort": "desc",
                    "type": "rightAligned",
                    "valueFormatter": {"function": "d3.format(',')(params.value)"},
                },
                {
                    "headerName": "Like Count",
                    "field": "like_count",
                    "width": 120,
                    "headerClass": "text-center",
                    "unSortIcon": True,
                    "type": "rightAligned",
                    "valueFormatter": {"function": "d3.format(',')(params.value)"}
                },
                {
                    "headerName": "Comment Count",
                    "field": "comment_count",
                    "width": 120,
                    "headerClass": "text-center",
                    "unSortIcon": True,
                    "type": "rightAligned",
                    "valueFormatter": {"function": "d3.format(',')(params.value)"}
                },
            ]
        },
        {
            "headerName": 'Searched At',
            "field": "inserted_at",
            "width": 120,
            "headerClass": "text-center",
            "unSortIcon": True,
            "cellStyle": {'textAlign': 'center'}
            # "valueGetter": {"function": date_obj},
            # "valueFormatter": {"function": f"d3.timeFormat('%Y/%m/%d')({date_obj})"}
        },
    ]

    return dag.AgGrid(
        id='content-grid',
        rowData=data,
        columnDefs=content_columnDefs,
        dashGridOptions={
            'pagination': True,
            'rowHeight': 90,
            "rowSelection": "single",
            "overlayNoRowsTemplate": "<span style=\"padding: 10px; border: 2px solid #444; background: lightgoldenrodyellow; \">This is a custom 'no rows' overlay</span>",
        },
        dangerously_allow_code=True,
        columnSize="sizeToFit",
        className="ag-theme-quartz",
        style = {"height": 800}
    )