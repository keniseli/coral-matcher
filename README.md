# Overview
This project aims to simply monitoring of coral colonies in the context of marine conservation. Users can upload photos taken of a coral colony. The application will identify which part of the image contains a colony and let the user decide whether it has guessed right. Then, the application will use embedding to find out whether it has seen this colony before and if so, show all the pictures history-style so that users can identify compare the colony's development with ease.



## Acknowledgements

### CoralSCOP
This project uses CoralSCOP, developed by Wong et al., for coral segmentation. It has proven to be extremely helpful for this project.

CoralSCOP:
https://github.com/zhengziqiang/CoralSCOP

Paper:
CoralSCOP-LAT: Labeling and Analyzing Tool for Coral Reef Images with Dense Mask

Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0):
https://creativecommons.org/licenses/by-nc-sa/4.0/

The Coral Matcher project integrates CoralSCOP as a preprocessing step for coral segmentation before colony matching. The only modifications have been made to integrate the model into this application (eg. adjusting imports and adding log statements for debugging purposes).

