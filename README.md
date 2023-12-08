# DSM_BE
5 tables:
* Above 3 tables are master tables: Assumption is to make it as a master object on front end within context manager:
1. categories
2. impacts_types
3. contributions

* Other two tables are transactional with db interactions to put items:
4. impact_details - for saving impacts within a category and the impact percent in the category.
5. impact_contributions - for saving how much percent category has contributed and how much other external details contributed.
==================================================================================================================================

We have 3 categories: 
All categories comes when there is -1 as category id passed in query params
1. Ingredients
2. Transportation
3. On-site resources

We have 4 impact types:
1. Air
2. Land
3. Human
4. Water

Assumption: We can have a calculation: Each KPI number is the avg value of value shown in the impact.But kept as some contant values just to make it look simple.
Assumption: each category has some impact on climate, land, human or water.

Whenever there is a new impact, there will not be any addition to the same categoryid and impact id, but it will change/update the impact detail.
Example json contract to save any category impact.

impact_details(category_id, impact_id-sort key): assuming if in future we want to query dta per category per impactid then would be beneficial.
{
"category_id": 1,
"impact_id": 1
"impact_name": "Climate change"
"impact_type": "air",
"impact_value": 100,
"impact_percent": 99
}

construbutions:(contribution_id) (Assumption: clubbed all 3 same contribution types: Another contribution category as one)
1. Soybean meal (solvent) from Netherlands
2. Maize gluten meal dried from Denmark
3. Feed coming from a certain country with a longer name
4. Another category
5. Another contribution category


impact_contributions:(impact_id, contrib_id_type sort key)
[{
"impact_id": 1,
"contrib_id_type": "1#1#other",// splitting composite sort key-> first is category_id and second is contrib_id and third is contrib_type
"contrib_value": 20
}

{
"impact_id": 1,
"contrib_type": "1#category",
"contrib_value": 20
}
]


final demo contract:
{
    "detail": [
        {
            "category_id": 1,
            "impact_id": 1,
            "impact_name": "Climate change - biogenic",
            "impact_type": "Air",
            "impact_value": 300,
            "impact_percent": 49
        }
    ],
    "contribution": [
         {
            "impact_id": 1,
            "contrib_id_type": "1#1#other",
            "contrib_value": 4
        },
		{
            "impact_id": 1,
            "contrib_id_type": "1#2#other",
            "contrib_value": 3
        },
		{
            "impact_id": 1,
            "contrib_id_type": "1#category",
            "contrib_value": 42
        },
    ]
}
