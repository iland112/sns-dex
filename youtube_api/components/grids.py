import dash_ag_grid as dag

def youtube_content_grid(data=None):
    """
    Create AG Grid component for youtube video contents records
    """
    content_columnDefs = [
        {
            "headerName": "No.",
            "valueGetter": {"function": "params.node.rowIndex + 1"},
            "width": 70
        },
        {
            "headerName": "Content Image",
            "field": "thumbnail",
            "width": 120,
            "cellRenderer": "VideoImageRenderer"
        },
        {
            "headerName": "Country",
            "field": "country",
            "width": 100,
            "cellRenderer": "CountyFlagRenderer"
        },
        {
            "headerName": "Video Title",
            "field": "video",
            "wrapText": True,
            "cellRenderer": "VideoIdRenderer"
        },
        {
            "headerName": "Channel Title",
            "field": "channel",
            "cellRenderer": "ChannelIdRenderer"
        },
        {
            "headerName": 'Published At',
            "field": "published_at",
            "width": 120,
            "cellStyle": {'textAlign': 'center'}
            # "valueGetter": {"function": date_obj},
            # "valueFormatter": {"function": f"d3.timeFormat('%Y/%m/%d')({date_obj})"}
        },
        {
            "headerName": "View Count",
            "field": "view_count",
            "width": 120,
            "type": "rightAligned",
            "valueFormatter": {"function": "d3.format(',')(params.value)"}
        },
        {
            "headerName": "Like Count",
            "field": "like_count",
            "width": 120,
            "type": "rightAligned",
            "valueFormatter": {"function": "d3.format(',')(params.value)"}
        },
        {
            "headerName": "Comment Count",
            "field": "comment_count",
            "width": 120,
            "type": "rightAligned",
            "valueFormatter": {"function": "d3.format(',')(params.value)"}
        },
        {
            "headerName": 'Searched At',
            "field": "inserted_at",
            "width": 120,
            "cellStyle": {'textAlign': 'center'}
            # "valueGetter": {"function": date_obj},
            # "valueFormatter": {"function": f"d3.timeFormat('%Y/%m/%d')({date_obj})"}
        },
    ]

    return dag.AgGrid(
        id='content-grid',
        rowData=data,
        columnDefs=content_columnDefs,
        dashGridOptions={'pagination': True, 'rowHeight': 90,},
        columnSize="sizeToFit",
        className="ag-theme-quartz",
        style = {"height": 800}
    )