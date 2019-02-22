# profpy.apis
## Overview
This module is an abstraction layer for accessing data from APIs with Python. As we use more of these APIs, we will update this documentation.
Each API will get its own class, which will be a child of the abstract class found in the utils/Api.py file. 

## Want to Contribute a new API to this repo?
New API-wrappers must be children of the Api parent class and implement all of its abstract methods. For a basic, overhead example
of this, checkout [the parent class' docs](./docs/Api.md). For more detailed implementations, you should look at the raw code for 
some of the currently maintained wrapper classes. 

## Current APIs 

Click links below to view documentation for currently maintained API wrapper classes
- [BlackBoard Learn API](./docs/BlackBoardLearn.md)
- [ServiceNow Table API](./docs/ServiceNowTable.md)
- [25Live API](./docs/TwentyFiveLive.md)

Other Useful Info:
- [Parent API Class Docs](./docs/Api.md)