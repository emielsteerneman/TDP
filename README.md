# ChatRTTETDP
ChatErTeeTeeeEEeeeDeeTeePee (name under development). Winner of the RoboCup 2023 Small Size League Open Source Award. 

We are all working towards the same goal: winning the World Championship of HUMAN soccer in 2050. What I love about the Small Size League is that, while we're opponents on the field, we're always ready to help develop and improve each other. I am not only referring to the teams that are currently here, but also all the teams that came before us. All of these teams are helping us by sharing their knowledge through the TDPs and ETDPs (317 papers and counting). Reading 317 papers is of course impossible. Therefore, to keep our inspiration and innovation going, RoboTeam Twente has made this information more accessible through a TDP/ETDP Search Engine. 

The search engine can be found on our website, https://tdp.roboteamtwente.nl/query. Also check out our Wiki https://wiki.roboteamtwente.nl/ and of course all our open-sourced software https://github.com/RoboTeamTwente/roboteam.

## Setup
```
$ pip install -r requirements.txt
$ python download_tdps.py
$ python fill_database.py 
$ flask run
```

## Docker
$ docker run -p 5000:5000 roboteamtwente/chatrttetdp:latest