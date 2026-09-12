# Philosophy

> To make coral restoration monitoring accessible so that we can save the world’s reefs step by step, coral by coral

Monitoring restored individual coral colonies often involves taking photographs in the field and then manually identifying, measuring, and comparing colonies across monitoring sessions. This is very time-consuming and certain approaches require high technical saviness. Coral Companion aims to tackle these issues.


# Overview
A typical workflow is:
1. Practitioner uploads one or many coral photograph(s)
1. Coral Companion detects and segments coral colonies
1. Practitioner reviews the detected segments and assigns the relevant colony to previous observations (or to a new coral colony)
1. Practitioner can review the colony's history across monitoring sessions and compare observations over time to help understand changes in the colony


## Roadmap
The long-term objective is to build a persistent history for individual coral colonies. This can support monitoring of metrics such as:
* colony growth
* survival and mortality
* partial tissue loss
* bleaching
* disease or other visible conditions
* changes in colony structure


# Acknowledgements

## CoralSCOP
This project uses CoralSCOP, developed by Wong et al., for coral segmentation. It has proven to be extremely helpful for this project. CoralSCOP has been cloned and its code is accessed under backend/third_party.

CoralSCOP:
https://github.com/zhengziqiang/CoralSCOP

Paper:
CoralSCOP-LAT: Labeling and Analyzing Tool for Coral Reef Images with Dense Mask

Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0):
https://creativecommons.org/licenses/by-nc-sa/4.0/

The Coral Companion project integrates CoralSCOP as a preprocessing step for coral segmentation before colony matching. The only modifications have been made to integrate the model into this application (eg. adjusting imports and adding log statements for debugging purposes).

