# System libraries
import asyncio
from collections import OrderedDict
import functools
import json
import os
import time
import threading
# Third party libraries
from flask import Flask, g, render_template, request, send_from_directory, Response
from telegram import Bot
# Local libraries
import app
import startup
from data_access.metadata.metadata_client import MongoDBClient
from data_access.file.file_client import FileClient
from data_access.vector.pinecone_client import PineconeClient
from data_access.vector.vector_filter import VectorFilter
from data_structures.TDPName import TDPName
from MyLogger import logger

flask_app = Flask(__name__, template_folder='webapp/templates', static_url_path='/static', static_folder='webapp/static')

metadata_client, file_client = startup.get_clients()
vector_client = PineconeClient(os.getenv("PINECONE_API_KEY"))

@flask_app.before_request
def before_request():
    g.file_client = file_client
    g.metadata_client = metadata_client

@flask_app.after_request
def after_request(response):
    # Add CORS headers
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

@flask_app.route("/")
def index():
    return "Hello World!!!"

@flask_app.route("/api/tdps")
def api_tdps():
    json_response:str = app.api_tdps()
    flask_response = Response(json_response)
    flask_response.headers['Content-Type'] = "application/json"
    flask_response.headers['Cache-Control'] = "max-age=604800, public"
    return flask_response

def api_tdp(tdp_name:str, is_pdf:bool=False):

    logger.info(f"API TDP {tdp_name} is_pdf={is_pdf}")

    try:
        tdp_name:TDPName = TDPName.from_string(tdp_name)
    except ValueError as e:
        logger.error(f"Invalid TDP Name {tdp_name}")
        raise ValueError(f"Invalid TDP Name {tdp_name}")

    if is_pdf:
        tdp_exists = g.file_client.pdf_exists(tdp_name)
    else:
        tdp_exists = g.file_client.html_exists(tdp_name)
    
    if not tdp_exists:
        logger.error(f"TDP {tdp_name} does not exist")
        raise Exception("TDP does not exist")

    if is_pdf:
        return send_from_directory("static/pdf", tdp_name.to_filepath(TDPName.PDF_EXT), max_age=604800)
    else:
        return send_from_directory("static/html", tdp_name.to_filepath(TDPName.HTML_EXT), max_age=604800)

@flask_app.route("/api/tdp/<tdp_name>/pdf")
def api_tdp_pdf(tdp_name:str):
    return api_tdp(tdp_name, is_pdf=True)

@flask_app.route("/api/tdp/<tdp_name>/html")
def api_tdp_html(tdp_name:str):
    return api_tdp(tdp_name, is_pdf=False)

@flask_app.route("/api/tdp/<tdp_name>/image/<image_idx>")
def api_tdp_image(tdp_name:str, image_idx:int):
    pass

@flask_app.route("/api/query")
def api_query():
    from search import search
    # Get query from URL
    query = request.args.get('query')
    filter = VectorFilter.from_dict(dict(request.args))

    myresponse = """[
  {
    "content": "A service robot is a robot that can assist humans to perform common daily tasks in a common environment, such as houses, offices or hospitals. With this in mind, the final goal of service robot must be make the life of humans easier and more comfortable. Also, a robot can be an excellent companion, in example for elderly or lonely people, making their life better and happier. To achieve this, a service robot must be capable of understanding spoken and visual commands in a natural way from humans, navigate in known and unknown environments avoiding static and dynamic obstacles, recognize and manipulating objects, detect and identify people, among several other tasks that a person might request. The team Pumas has participated in national and international competitions. In this year, in the Robocup 2018, our team obtenied the second place in the categoty DSPL@Home with the robot Takeshi and we were finalist in World Robot Summit(WRS) 2018. 2. TAKESHIS ROBOTICS ARCHITECTURE The paper is organized as follows: section 2 enumerates the software components of our robot Takeshi; section 3 presents overview of the latest research developments in our laboratory; and finally, in section 5, the conclusions and future work are given.",
    "questions": [
      "How can a service robot improve the quality of life for humans?"
    ],
    "tdp_name": {
      "index": 0,
      "league": {
        "league_major": "athome",
        "league_minor": "domestic",
        "league_sub": null,
        "name": "athome_domestic",
        "name_pretty": "@Home Domestic"
      },
      "team_name": {
        "name": "Pumas",
        "name_pretty": "Pumas"
      },
      "year": 2019
    },
    "title": "1 Introduction"
  },
  {
    "content": "We created a custom simulator that can simulate basic physics such as collisions and ball friction, as well as robot actions (movement, dribbling, and kicking). The simulator is designed to enable offline prototyping, by replacing both the vision provider and the radio provider in the modular setup. The simulator pretends we have a full team of robots operating under ideal conditions. Although it cannot model the real world fully, it has been useful for testing state machine logic and strategic evaluation. (Furthermore, combining its use with a custom visualizer has given us more flexibility than adopting an existing simulator such as GRSim). So far, rudimentary handling of the following items have provided enough realism for basic prototyping: 1. Ball Friction: The simulator estimates the ball velocity from historical timestamped positions stored in the gamestate, and assumes that the ball will continue in the same direction with constant deceleration. We found that inferring ball velocity from two past data points must interpret the change in position as the velocity at the midpoint of those two timestamps. Otherwise, applying deceleration across many small timesteps (as the simulator does) will not give accurate results. 2. Robot Collision: We do a frame-based check of each robot, and move overlapping robots away from each other by equal amounts to resolve collisions. 3. Ball collision: In each frame, when the ball intersects with a robot we move the ball outside the robot, and preserve the component of its velocity that was tangent to the robot model (which is a circle with a flat front face). 4. Robot Movement: Each robot moves at exactly the speed of the given vector command. (Note: this results in slower convergence to waypoints than in real life, so we hope to improve this model by incorporating acceleration limits) 5. Dribbling: We model dribbling by moving the ball towards the center of the robot when it is within a small distance of the robots dribbler location. There is a threshold speed above which the ball is not dribbled, to avoid unrealistic capturing of the ball. 6. Charging + Kicking: Robots given command to charge will simulate increasing charge level. When given the command to kick we apply a velocity to the ball in the direction of the robot, if it is in a small radius of the kicker.",
    "questions": [
      "What benefits does using a custom simulator provide over existing simulators for testing state machine logic and strategic evaluation?",
      "How does the team handle ball collision and robot movement in their gameplay?"
    ],
    "tdp_name": {
      "index": 0,
      "league": {
        "league_major": "soccer",
        "league_minor": "smallsize",
        "league_sub": null,
        "name": "soccer_smallsize",
        "name_pretty": "Soccer SmallSize"
      },
      "team_name": {
        "name": "RFC_Cambridge",
        "name_pretty": "RFC Cambridge"
      },
      "year": 2020
    },
    "title": "3.3 Simulation"
  },
  {
    "content": "High level defensive techniques used in real life soccer were incorporated into the teams defense. In real life soccer, there are two basic objectives that need to be balanced [4]. The first is slowing down opponents play. This allows more time for the entire defense to move into position as well as eliminate many of the quick passing plays that are extremely difficult to defend against. The second objective is pushing opponents into making suboptimal decisions that are difficult to execute successfully. Slowing down the offensive push can be done through overall positioning. In a real life 4-man defense, there is a diagonal that sweeps across the field shown in Figure 8. The specific positioning of the robots block the dangerous through passes while still leaving the defending robots in a position to react to other actions. Pushing opponents into suboptimal decisions can be done through marking the offensive players on an inside angle as shown by player 3 marking striker A in Figure 8. 8",
    "questions": [
      "How can defensive strategies in real life soccer be applied to robot soccer teams?"
    ],
    "tdp_name": {
      "index": 0,
      "league": {
        "league_major": "soccer",
        "league_minor": "smallsize",
        "league_sub": null,
        "name": "soccer_smallsize",
        "name_pretty": "Soccer SmallSize"
      },
      "team_name": {
        "name": "RoboJackets",
        "name_pretty": "RoboJackets"
      },
      "year": 2018
    },
    "title": "3.4 Mirroring Real Life Defense"
  },
  {
    "content": "Automatic Simulator Grounding. Simulators inherently fail to capture the complexity of real physical robots. To address this, we are using recordings from from complex simulations and the real robots to improve the realism of state transitions in the abstract simulator. This research matters for Robocup because if an abstract simualtor can be made to more closely match the transition dynamics of the real robots, it should create policies which work better with the physical robots.",
    "questions": [],
    "tdp_name": {
      "index": 0,
      "league": {
        "league_major": "soccer",
        "league_minor": "standardplatform",
        "league_sub": null,
        "name": "soccer_standardplatform",
        "name_pretty": "Soccer StandardPlatform"
      },
      "team_name": {
        "name": "BadgerBots",
        "name_pretty": "BadgerBots"
      },
      "year": 2023
    },
    "title": "2."
  },
  {
    "content": "Our team builds a complete processing system which is capable of receiving information, processing information, making decisions and executing. This system is the brain and center that supports our game. It can be used in real robot races and simulation races and tests . In both modes, the processing flow of this system is roughly the same, and the performance is equally excellent. Now let us introduce the workflow of our system in two modes. In simulation mode, we use a simulator called grsim [3]. Its a 3 D simulator, which can generate robots simulated physical actions and simulated vision messages, and calculate collisions. After generating information about the game (such as simulated vision messages, state of movement), it sends those to an interactive software called owl . This software can display the simulation game progress and the on-court conditions, while it can also integrate several functional plugins listed as follows: The first is a plug-in called Vision Fuser , which is used to process and fuse the original vision messages transmitted, including noise reduction processing, filtering, etc. The second plug-in is the referee box , which can replace referees in real matches and issue referee instructions for test purposes. The third plugin is log , which can generate User Log Files and record vision messages processing. The last plugin is called GUI to display debug information, including the target point of each robot, some important auxiliary lines (connection to the opposite goal from our goal), value of ball speed, etc. This information can help us better judge what is happening on the field. After processing by Vision Fuser , the system will send fused vision messages to our calculating and operating system called rbk . This system can make decisions based on the data received and send instructions for the next steps. In simulation mode, these action instructions will be sent to grsim for further simulated actions.",
    "questions": [
      "What is the overall workflow of the system in both simulation and real robot races?"
    ],
    "tdp_name": {
      "index": 0,
      "league": {
        "league_major": "soccer",
        "league_minor": "smallsize",
        "league_sub": null,
        "name": "soccer_smallsize",
        "name_pretty": "Soccer SmallSize"
      },
      "team_name": {
        "name": "SRC",
        "name_pretty": "SRC"
      },
      "year": 2020
    },
    "title": "4 Overall technical/software framework"
  },
  {
    "content": "For object recognition we have two approaches, one off-the-shelf and the second which we are developing ourselves. The of-the-shelf method uses YOLO [ ? ] to detect objects in the scene, placing bounding boxes around them and the using the point cloud from the RGB-D camera to locate the object in space. When attempting to grasp the object, we used ROS packages for finding the grasp points and planning the arm movement. We have also developed model-based approaches to 3D object recognition using RGB-D cameras. The vision system extracts shape primitives (e.g. planes and cylinders) from the point cloud. A relational learning system then builds a description of the object class based on the relationships between the shape primitive [5]. This method has been used in the rescue environment to recognise Short-Term Memory Long-Term Memory Manipulation Navigation Perception Mapping Planning Dialogue Manager Fig. 1. Software architecture of UNSW@Home staircases and other terrain features. Once a model of the object is created, it is imported into a simulator, like Gazebo, which allows the robot to visualise actions before executing them in the real world. We are also investigating other applications of logical vision [6].",
    "questions": [
      "What simulator is commonly used by robotics teams to visualize actions before executing them in the real world?"
    ],
    "tdp_name": {
      "index": 0,
      "league": {
        "league_major": "athome",
        "league_minor": "domestic",
        "league_sub": null,
        "name": "athome_domestic",
        "name_pretty": "@Home Domestic"
      },
      "team_name": {
        "name": "UNSW",
        "name_pretty": "UNSW"
      },
      "year": 2019
    },
    "title": "2.4 Object Recognition and Grasping"
  },
  {
    "content": "Robotics is one of the fastest growing areas in the world. New technologies arise at all times and it is undeniable that the future will have the increasingly striking presence of robots in our daily lives. The Rinobot-Jaguar Team, armed with a feeling of growth and innovation, seeks through research and testing, always improve and optimize game strategies. The Robocup championship, worldwide, has the potential to give more prestige and visibility to the teams efforts, encouraging companies and potential employees to sponsor the team, enabling the continuity of the project. It will be extremely important for the Brazilian teams that make up the team, because contact with more advanced technologies would contribute greatly to the educational development of the team, in addition to encouraging and strengthening research in this area, in national territory, and being able to put into practice everything we have developed so far. At Rinobot, the team places a strong emphasis on community outreach. They regularly visit local schools to showcase their robots and introduce children and teenagers to the exciting world of robotics. This is especially important as robotics is still relatively underexplored in basic education, and the team believes in inspiring young minds to pursue careers in this field. Overall, both the Rinobot and the Jaguar teams are dedicated to advancing the field of robotics through their passion for innovation and their commitment to community outreach. The teams participation in the Robocup is a key component of their mission, as it provides a platform for showcasing their work and advancing the field as a whole.",
    "questions": [
      "In what ways can advancements in robotics technology impact the future of daily life?"
    ],
    "tdp_name": {
      "index": 0,
      "league": {
        "league_major": "soccer",
        "league_minor": "standardplatform",
        "league_sub": null,
        "name": "soccer_standardplatform",
        "name_pretty": "Soccer StandardPlatform"
      },
      "team_name": {
        "name": "Rinobot_Jaguar",
        "name_pretty": "Rinobot Jaguar"
      },
      "year": 2023
    },
    "title": "5 Impact"
  },
  {
    "content": "Most of our work has been based on simulation. In order to keep our simulator consistent with the real world and not get biased results, we worked towards more realistic modeling. Most of the work has been in improving ball behavior better friction models and realistic deflection from robots. The only hurdle in this respect is modeling deflections off the front of the robot, where the movable dribbler makes modeling non-trivial. We are also working on more realistic dynamic robot models to be incorporated in the simulator.",
    "questions": [
      "How did the team work towards more realistic modeling in their simulator?"
    ],
    "tdp_name": {
      "index": 0,
      "league": {
        "league_major": "soccer",
        "league_minor": "smallsize",
        "league_sub": null,
        "name": "soccer_smallsize",
        "name_pretty": "Soccer SmallSize"
      },
      "team_name": {
        "name": "RFC_Cambridge",
        "name_pretty": "RFC Cambridge"
      },
      "year": 2011
    },
    "title": "4.3.1 Realism"
  },
  {
    "content": "In order to make autonomous mobile robots on a custom platform, a lot of work needs to be done to make all robot systems made by different manufacturers to work together. This paper described how a robot architecture looks like after a year of work with no much prior experience in robotics. Still, after a lot of hard work and team work, a working well designed robot using simple tactics is possible to make when following previous work from other teams and information available online in robotics area. In future, a more robust localization system that does not depend on outside active beacons is to be made along with implementing the other rules from Robocup MSL rulebook in order to build fully autonomous soccer playing robots in near future that would be able to beat humans in a game of soccer.",
    "questions": [
      "How important is teamwork in developing a well-designed robot for the Soccer MidSize league?"
    ],
    "tdp_name": {
      "index": 0,
      "league": {
        "league_major": "soccer",
        "league_minor": "midsize",
        "league_sub": null,
        "name": "soccer_midsize",
        "name_pretty": "Soccer MidSize"
      },
      "team_name": {
        "name": "UM-Croatia",
        "name_pretty": "UM-Croatia"
      },
      "year": 2023
    },
    "title": "5 Conclusion"
  },
  {
    "content": "Applicability in the real world Research is conducted in an attempt to understand how humans react in the interactive process with robots, but it is difficult to capture the real feelings of the human during the construction of tasks shared between the robot and the people in the scenario. As the computer can understand our human reactions, feelings, emotions and social relationships, it can then better understand what actions to take in various everyday situations in an environment of human interaction at work, at home or in a hospital for example. Results For the validation of the module two main parts were analyzed, being one of them the statistical data of the training and the validation of the classifier used, and the other part the application of the module in real time in the humanrobot. The experiment was initially done with ten subjects and Table 1 shows the accuracy of the best result obtained from the training and validation of the implemented classifier, where it is possible to see the percentage of correctness of the classifier for each class. Table 1 shows the trained classes for emotional states, happiness, sadness and neutrality, respectively, represented by numbers 1, 2 and 3.",
    "questions": [
      "Why is it difficult to capture the real feelings of humans during tasks shared with robots?"
    ],
    "tdp_name": {
      "index": 0,
      "league": {
        "league_major": "athome",
        "league_minor": "open",
        "league_sub": null,
        "name": "athome_open",
        "name_pretty": "@Home Open"
      },
      "team_name": {
        "name": "RoboFEI",
        "name_pretty": "RoboFEI"
      },
      "year": 2019
    },
    "title": "4.4 Module for Human-Robot Adaptive Interaction Using"
  },
  {
    "content": "The focus of our AI team is on developing a good defense system for this year. In simulations, we have been testing our algorithms and methods. Translating the AI onto the real robots has been a challenge due to the many variables involved in accurate robot motion. This lead us to start work on improving the motion control of the robot. We have added high resolution encoders to our metal bases and are working on improving the motion control of the robots. As seen in the defense section of the qualification video, the robots have improved motion. According to our implementation plan, the robots will have very reliable motion control by April, and will enable us to have a good defense AI for RoboCup 2017.",
    "questions": [
      "How did the AI team for the Anorak team in 2017 work on improving the motion control of the robots?"
    ],
    "tdp_name": {
      "index": 0,
      "league": {
        "league_major": "soccer",
        "league_minor": "smallsize",
        "league_sub": null,
        "name": "soccer_smallsize",
        "name_pretty": "Soccer SmallSize"
      },
      "team_name": {
        "name": "Anorak",
        "name_pretty": "Anorak"
      },
      "year": 2017
    },
    "title": "4.1 Focus on Defense Strategies"
  },
  {
    "content": "The robot uses brushless motor, 50 watts Maxon EC45 flat, in the driving system. The motion system uses external gear with ratio of 1:3.6. This kind of motor and the mentioned gear ratio can provide more acceleration and velocity than our previous one. The motor of robot is connected to a 360 CPR optical encoder for speed measurement. Each encoder is connected to the motors with a custom-made intermediate plate. We used 5mm thick Aluminum Alloy 6061 plate as a chassis. This plate connects all the parts together, such as motors stand, direct solenoid and etc. Fig. 32 shows our robot in Iran open2011 competitions. 0 50 100 150 200 250 300 350 1 2 4 Distance(cm) Distance of ball handeling for different materials of spin back bar Polyurthane Silicon Carbon Sillicon 4 Motion Control Control section contains two main parts; Motor control that concerns about each wheel of robots to work at the desired performance, and motion control on each robot to move on the desired trajectory with desired velocity profile.",
    "questions": [
      "How does the motion system of the robot work?"
    ],
    "tdp_name": {
      "index": 0,
      "league": {
        "league_major": "soccer",
        "league_minor": "smallsize",
        "league_sub": null,
        "name": "soccer_smallsize",
        "name_pretty": "Soccer SmallSize"
      },
      "team_name": {
        "name": "MRL",
        "name_pretty": "MRL"
      },
      "year": 2011
    },
    "title": "4.4. Motion system"
  },
  {
    "content": "Diagram depicted in Figure 12 shows a general overview of the system, where we implement a high level AI decision making in order to decide which is the best action to take from a set of preprogrammed plays based on the game state that comes just from the vision receiver. Then we have a low level path planning algorithm to choose the best path in order to execute the play avoiding obstacles. This is implemented on the desktop computer in charge of making the centralized decisions for every robot.",
    "questions": [
      "How does a high level AI decision-making system work in robot soccer?"
    ],
    "tdp_name": {
      "index": 0,
      "league": {
        "league_major": "soccer",
        "league_minor": "smallsize",
        "league_sub": null,
        "name": "soccer_smallsize",
        "name_pretty": "Soccer SmallSize"
      },
      "team_name": {
        "name": "AIS",
        "name_pretty": "AIS"
      },
      "year": 2018
    },
    "title": "6 Software"
  },
  {
    "content": "Of course, such high level decision makings can be implemented properly when each task in lower levels could be performed in a perfect manner. Before obtaining such performances a simulator will help the high level designer to evaluate his ideas (fig. 9). The core system of MRL2011s simulator is the same as MRL2010. One of the significant changes in the simulator is considering noise signals in wireless system. We found that this noise has a close relation with distance. Sometimes data packets arent properly received by robots. A probabilistic model for data transfer has been introduced to simulate a real wireless system. Measuring lost data compared with the size of sent packets shows a detectable relation with distance between the robot and the wireless transmitter ( d ). A Gaussian distribution is fitted to the wireless noise with the mean ( m ) and variance ( related to the distance ((1) and (2)). More details about these contributions are explained in [1]. (1) (2) Because of latency in finalizing the robot hardware structure, investigation of the codes from high level strategies to each skill performance need an environment similar to the reality. Fortunately, progressing of the simulator prepared such an environment and our tests in simulator not only specified our bugs but also give some new points about implementation on real robots. Besides these preferences, this mechanism prevents the robots from damaging. As stated before, our learning algorithms after evaluating on the simulator made an appropriate basin to converge in real world. Another point is about the analyzer which simplifies our operations as much as possible. From availability of changing the game strategy to demonstration of the game status and drawing the diagrams and necessary shapes to analyze the game conditions and detect the mistakes are achievable with this tool. In near future we will complete the entire requirements to play with a team of the robots with a virtual team in the simulator that satisfy our need to have friendly matches.",
    "questions": [
      "What are the advantages of testing on simulators before deploying algorithms on real robots?"
    ],
    "tdp_name": {
      "index": 0,
      "league": {
        "league_major": "soccer",
        "league_minor": "smallsize",
        "league_sub": null,
        "name": "soccer_smallsize",
        "name_pretty": "Soccer SmallSize"
      },
      "team_name": {
        "name": "MRL",
        "name_pretty": "MRL"
      },
      "year": 2012
    },
    "title": "2.3.2 Regioning:"
  },
  {
    "content": "Omni-vision systems using mirrors are used by most of the teams for localization using the field lines and for opponent and ball detection and positioning. In 2019, our team also built an omni-vision system using a revolution mirror. If these systems are relevant for finding the ball, they have some drawbacks for positioning our robot. A major one is the need for a precise alignment of the mirror and the camera. A small (less than 0 . 5 mm ) misalignment involve an important distortion in the omni-vision image leading to a wrong positioning. A second one, related to the first one is that the size of the field lines located far from the robot is very small in the image. Consequently positioning of the omnidirectional optical axis in a perfectly vertical direction is also very important. These drawbacks are limitations to the use of these omnidirectional systems. It is still possible to cope with them when playing on a green flat carpet, but it would be very difficult to cope with them when playing in real conditions such as the soccer field in Fig. 7. In this case, the robot couldnt be horizontal at any time and the lines are occluded by mud and field irregularities. This demonstrates that positioning using omni-vision is probably not a robust and reliable option in a long term view, if we want to play against humans in real conditions. Consequently, the important question is : what is a robust soccer positioning based on ? An answer to this question can be found by looking again to the picture 7. The view is a soccer player one. In this case, just by seeing the scene, a soccer player can tell that he is approximately at 30 35 m from the goal and can evaluate it positioning zone quite precisely. This human evaluation does not use the field lines, which are difficult to see. The most important information is the place and appearance of the goal in the image, and on the perception of depth using stereovision.",
    "questions": [
      "What are the challenges of robot positioning in real soccer field conditions?"
    ],
    "tdp_name": {
      "index": 0,
      "league": {
        "league_major": "soccer",
        "league_minor": "midsize",
        "league_sub": null,
        "name": "soccer_midsize",
        "name_pretty": "Soccer MidSize"
      },
      "team_name": {
        "name": "RCT",
        "name_pretty": "RCT"
      },
      "year": 2022
    },
    "title": "4 A new method for positioning and detecting balls and opponents"
  },
  {
    "content": "Skills allow state to be kept because skills are objects with private data, not just functions as used in the past. In addition, skills provide various methods for initialization, running, loading and reloading parameters, and much more. Role is a combo set of skills that call by each position, such as ForwordRole or GoalieRole. By the way, both plays and positions can call skill directly but it will complicate if they have many states. Roles are object that inherit from skill, so they have same properties with skill. There exist four robot positions on the field Blocker, Defender, Aggressor, and Creator. The fifth robot position is called SpecialOp that can take on one of three dutys: SpecialOpDefender, SpecialOpAggressor, or SpecialOpCreator. The Blocker remains in the defense zone the majority of the time, only venturing slightly outside of it at times. The Blocker is the only position that will try to grab the ball when inside of the goalie box. The Defender is a dedicated position to the defense. The defender always remains on our side of the field, almost entirely in the defense zone, and works with or supplements the actions of the blocker, stopping shots or closing holes whenever possible. The Aggressor is the most active player on the field. See a robot who has the ball, he's undoubtedly the aggressor. See a robot go up to an opponent who has the ball, either to screen him from our goal or strip the ball away, that is the aggressor. The Creator is our dedicated robot to creating opportunities. The creator spends the majority of his time far upfield, either in the kill zone, offensive zone, and sometimes as low but never lowers than the death zone. The SpecialOpDefender acts as an auxiliary defender. When available, the SpecialOpDefender may screen auxiliary opponents who are coming down the field from getting near the ball. He may also help block passes or shots on goal.",
    "questions": [
      "How do various robot positions work together to achieve team goals?"
    ],
    "tdp_name": {
      "index": 0,
      "league": {
        "league_major": "soccer",
        "league_minor": "smallsize",
        "league_sub": null,
        "name": "soccer_smallsize",
        "name_pretty": "Soccer SmallSize"
      },
      "team_name": {
        "name": "Skuba",
        "name_pretty": "Skuba"
      },
      "year": 2009
    },
    "title": "6.3.2 StrategyModule"
  },
  {
    "content": "Improving team strategy is one of the main goals of this year for our team. Our goal is to let the robots decide what could be their best action according to team rules (such as one player maximum contesting a ball) and to the other potential robot actions. An algorithm has been developed, based on the idea that we will play with humans in a near future, and consequently humans can not send their real position, perception and chosen actions to their robot teammates. This means, each robot has to imagine what could be their best action and their teammates best actions in order to make a choice. In order to increase the flexibility of each robot and to improve the interoperability between the robots in different scenarios, several possible actions for each robot has been defined (Table 2). Action A1 Stopped A2 GoalKeeping A3 RushToGoal A4 TryToCatchBall A5 TryToPassBall R1-4 (A5-A8) Try to pass on to teammates i, ( i = 1 ... 4) A6 TryToShoot P1-4 (A9-A12) Try to kick the ball into one of the four-goal positions A7 CloseAssist Move closer to support teammates who have the ball A8 UnMarking Unmark A9 BlockShooting R1-4 (A15-A18) Move to be able to cut the ball of the opponent A10 BlockPass R1-4 (A19-A22) Move to block the direction of the opponents movement Table 2. List of possible actions (to be expanded or reduced) Action selection algorithm is described at Figure 7. Every 20ms, the following steps are done : Step 1: game situation is determined, based on the game state from the referee box and the team ball handling status computed by aggregating ball handling information from each player. Step 2: according to the game situation, each robot computes a list of possible actions for itself and for other teammates (approximately 300 in real conditions).",
    "questions": [
      "How does the team handle communication between robots without receiving real position, perception, and chosen actions from humans?"
    ],
    "tdp_name": {
      "index": 0,
      "league": {
        "league_major": "soccer",
        "league_minor": "midsize",
        "league_sub": null,
        "name": "soccer_midsize",
        "name_pretty": "Soccer MidSize"
      },
      "team_name": {
        "name": "RCT",
        "name_pretty": "RCT"
      },
      "year": 2023
    },
    "title": "3.3 Strategy"
  },
  {
    "content": "Modeling basically models the world state. It executes probabilistic stochastic filters to determine where the robot is in the field, and where the other agents are. Modeling is divided in two parts, a World Model and an Agent Model. Agent Model The Agent Model models information related to the robot itself. It computes transformation matrices which are used to transform vision observations from the camera coordinate system to a coordinate system on the ground. World Model The World Model is responsible for modeling world states such as game state, time, and position, so that this information can be used by Decision Making. It runs the Localization algorithm in order to estimate the robots position.",
    "questions": [
      "How does modeling work in a soccer simulation robotics team?"
    ],
    "tdp_name": {
      "index": 0,
      "league": {
        "league_major": "soccer",
        "league_minor": "simulation",
        "league_sub": "3d",
        "name": "soccer_simulation_3d",
        "name_pretty": "Soccer Simulation 3D"
      },
      "team_name": {
        "name": "ITAndroids",
        "name_pretty": "ITAndroids"
      },
      "year": 2022
    },
    "title": "2.3 Modeling"
  },
  {
    "content": "The main routine is divided into 5 major steps: decide an intention, such as moving to a point, dribbling, kicking, get up, etc; then choosing a skill, since some intentions can require different skills for positioning and execution; computing a target for the current skill, including a desired position or orientation, according to the skill requirements; execute the skill through a neural network or slot behavior; and finally broadcast information as explained in Section 2.3. When the robot is standing, deciding an intention requires an analysis of promising passes, shooting directions and dribbling paths. The algorithm scores the potential outcomes to estimate what would be the best alternative for game progression. If none of these options is viable, the robot will push the ball by walking towards it until it has enough space to take other actions.",
    "questions": [
      "How does the decision-making process work for robots in Soccer Simulation 3D?"
    ],
    "tdp_name": {
      "index": 0,
      "league": {
        "league_major": "soccer",
        "league_minor": "simulation",
        "league_sub": "3d",
        "name": "soccer_simulation_3d",
        "name_pretty": "Soccer Simulation 3D"
      },
      "team_name": {
        "name": "FC_Portugal_3D",
        "name_pretty": "FC Portugal 3D"
      },
      "year": 2022
    },
    "title": "2.6 Main Routine"
  },
  {
    "content": "We have created two algorithms for speed control. Each of them has its advantages and disadvantages. The reason why we need two different algorithms is in that we worked with two generations of robots. The old (1st generation) robots were not made high precision and drove at different speeds. This is expressed in different times of overcoming the same distance with the same values of speed parameters. For such robots, it was necessary to create special software functions that would synchronize the work of all robots and their characteristics. There is no such problem for the second generation. New robots move at the same real speed, and such software settings are no longer needed. Thus, we have two algorithms, because one of them is necessary for the first generation of robots, and for the new one it is simply redundant. Algorithm 1 . Robot moves from point A to point B along a straight line. Denote by x ( t ) the distance of the robot from the point A at time t . The following restrictions are imposed: | x ( t ) | < w acceleration limitation | x ( t ) | < v speed limitation (1) We assume that the constants w and v are known to the controller designer. Then it will be optimal for robot to accelerate as long as possible, afterwards go with full speed and in the end slowing down as fast as possible. In this way absolute speed graph looks like trapezoid. Denote by x ( t ) the function describing such movement. Apparently, it is a function, for which we may choose parameter values T w < T v < T necessary to describe the following relations: x ( t ) = w for t [0 , T w ] constant acceleration segment x ( t ) = v for t [ T w , T v ] constant speed segment x ( t ) = w for t [ T v , T ] constant deceleration segment x ( t ) = 0 for t > T Denote the control function by u ( t ). Then the model is described by the following equation x ( t ) = C u, (2) where C is an unknown constant that may be different for different robots in the team.",
    "questions": [
      "Why is it important to synchronize the work of robots and their characteristics in a team?"
    ],
    "tdp_name": {
      "index": 0,
      "league": {
        "league_major": "soccer",
        "league_minor": "smallsize",
        "league_sub": null,
        "name": "soccer_smallsize",
        "name_pretty": "Soccer SmallSize"
      },
      "team_name": {
        "name": "URoboRus",
        "name_pretty": "URoboRus"
      },
      "year": 2022
    },
    "title": "5.2 Two approaches to speed control"
  },
  {
    "content": "We use the Xbee module to control the robots wirelessly, and the robots can apply power to the wheels. Then the robots can work like in the simulator used.",
    "questions": [],
    "tdp_name": {
      "index": 0,
      "league": {
        "league_major": "soccer",
        "league_minor": "smallsize",
        "league_sub": null,
        "name": "soccer_smallsize",
        "name_pretty": "Soccer SmallSize"
      },
      "team_name": {
        "name": "UNSAbots",
        "name_pretty": "UNSAbots"
      },
      "year": 2014
    },
    "title": "3.1 Distributed Control"
  },
  {
    "content": "6 To compute the desired final step displacement while the robot is moving, two key features are needed. First, the ball relative pose with respect to the robot must be estimated from the camera while carefully taking into account the vision processing delay. Second, the final step computation is only sent to the walk engine at the end of the current step (to be applied at the next (half) walk cycle). Because of this, the future robot pose with respect to the ball at the end of the current walk cycle must be also correctly estimated. Note that because the robot comes to full stop after this last step, it turns out than a step distance larger than usual can be applied without jeopardizing the balance of the robot. This procedure is actually a first work toward a proper steps planning strategy to optimize the several final steps with respect to stepping limits and possibly obstacles. A model predictive control (MPC) scheme is currently being experimented. The current implementation assumes that the desired step kinematically computed is tracked and realized on the real robot. However, our past experiments on odometry showed that this is a very coarse approximation (position control error, foot sliding, joint backlash). The predictive displacement model studied and devised in [5] should be used here to encompass the reality gap.",
    "questions": [
      "What challenges are faced when tracking and realizing the desired step kinematically computed on the real robot?"
    ],
    "tdp_name": {
      "index": 0,
      "league": {
        "league_major": "soccer",
        "league_minor": "humanoid",
        "league_sub": "kid",
        "name": "soccer_humanoid_kid",
        "name_pretty": "Soccer Humanoid Kid"
      },
      "team_name": {
        "name": "Rhoban_Football_Club",
        "name_pretty": "Rhoban Football Club"
      },
      "year": 2019
    },
    "title": "5.2 Ball Approach"
  },
  {
    "content": "The RoboCup is a robot competition for international students and scientists initiated in 1997. Initially the robots were built and programmed to play football. To stress the propagation of robotics in our everyday life, several other competitions were created during the last years. To represent industrial robot applications, the RobotCup Industrial with its two leagues Logistics and @Work was established. Whereas teams in the RoboCup@Work League have to handle several different work pieces to simulate industrial production scenarios, the RCLLs focus is on intra-logistic challenges and the robots have to handle standardized work pieces. The standardized systems used in the RCLL are Robotino robots and Modular Production Stations (MPS) by Festo Didactic. During gameplay two teams share one playing field. Each team is allowed to play with three robots. The MPSs are placed randomly on the field, whereas each team has its own set of MPSs. As a third component the Referee Box (refbox) provides each team the current information about the game phase and especially the orders of the products, which need to be produced by the teams robots. In the first phase of the gameplay, the exploration phase, the robots have to find the teams MPSs and report their positions to the refbox. During the second phase, the production phase, the robots have to produce the ordered work pieces using the MPSs. The work pieces are simple cylindrical parts, composed of a base, a cap and ring elements. The complexity of the products can be varied by using up to three ring elements. During production phase the robots are used to transport the products to the MPSs. The actual production is done by the MPS. Each team has one Base Station (BS), which provides the base elements to the robots. The rings are placed onto the base element by the Ring Station (RS). The Cap Station (CS) puts the final cap on top of the product. Each team has two RS and two CS. Finally, the product needs to be transported to the Delivery Station (DS). Since 2017 a fifth station, the Storage Station (SS), has been introduced. The SS allows to store several products.",
    "questions": [
      "How has the gameplay in the RCLL changed since 2017?"
    ],
    "tdp_name": {
      "index": 0,
      "league": {
        "league_major": "industrial",
        "league_minor": "logistics",
        "league_sub": null,
        "name": "industrial_logistics",
        "name_pretty": "Industrial Logistics"
      },
      "team_name": {
        "name": "ER-Force",
        "name_pretty": "ER-Force"
      },
      "year": 2019
    },
    "title": "2 RoboCup Logistics League"
  },
  {
    "content": "For testing purposes, a simulator is being developed. So, very soon we will be testing in a realistic simulation environment, which can provide feedback close to real robots. The use of a simulator is justified not to risk the integrity of robots with code that has just been written, and avoids the overhead of integration with other areas, field installation and maintenance of robots required for the physical tests. This simulator is developed in C++.",
    "questions": [],
    "tdp_name": {
      "index": 0,
      "league": {
        "league_major": "soccer",
        "league_minor": "smallsize",
        "league_sub": null,
        "name": "soccer_smallsize",
        "name_pretty": "Soccer SmallSize"
      },
      "team_name": {
        "name": "RoboPET",
        "name_pretty": "RoboPET"
      },
      "year": 2010
    },
    "title": "3.3 Simulation"
  },
  {
    "content": "In case of a RotatingTable subtask, before grasping an object, a preprocessing step to determine objects velocity and pose in the table is required (section 4.5). Once the manipulation subtask is finished, the robot moves away from the service area and returns to the stateNextSubtask that will manage the following subtask to do. In addition, most of the states have error handling behaviors that manage recovery actions such as in case a navigation goal is not reachable, an object cannot be found or a grasping was unsuccessful. It is important to notice these failures and react to them by repeating the action or triggering planning modifications. The state machine framework can be found on GitHub under our laboratorys repository. 2",
    "questions": [
      "How does the robot handle errors and failures during manipulation subtasks in the Industrial @Work league?"
    ],
    "tdp_name": {
      "index": 0,
      "league": {
        "league_major": "industrial",
        "league_minor": "atwork",
        "league_sub": null,
        "name": "industrial_atwork",
        "name_pretty": "Industrial @Work"
      },
      "team_name": {
        "name": "AutonOHM",
        "name_pretty": "AutonOHM"
      },
      "year": 2019
    },
    "title": "4.1 State Machine"
  },
  {
    "content": "Our AdultSize robot Walker is a completely autonomous humanoid robot, with 1 camera, 2 gyros and 22 actuators integrated on body, controlled by RT-Linux and Jetson TX2, it can overcome the odds (soft grass field, other robot pushing and long time walking) and behave like a real strong man when shooting and blocking the ball. In this paper, we present the specifications and functions of Walker with the work of gait planning and control.",
    "questions": [],
    "tdp_name": {
      "index": 0,
      "league": {
        "league_major": "soccer",
        "league_minor": "humanoid",
        "league_sub": "adult",
        "name": "soccer_humanoid_adult",
        "name_pretty": "Soccer Humanoid Adult"
      },
      "team_name": {
        "name": "Tsinghua_Hephaestus",
        "name_pretty": "Tsinghua Hephaestus"
      },
      "year": 2019
    },
    "title": "7 Conclusion"
  },
  {
    "content": "We divide the robot system into a three subsystems with a corresponding subteam: Mechanical designs and builds the physical robot chassis, drive components, kicking/chipping mechanisms, and mounting all of the electrical hardware within the robots. They are also responsible for engineering the placement of all components, both electrical and mechanical, within the robot. Electrical designs and builds the control circuitry for the robots. This includes the motor driver modules, the kicker solenoid system, and the radio communications modules. Software handles control of the robots from the main computer, including world modeling, low-level control, and high-level strategy and planning. While each subteam can work on a particular segment of the project, many zones necessitate signi cant collaboration between the subteams, such as accounting for electrical considerations in design of the kicker & chipper systems, or sensor integration relevant to control approaches. There are two main phases of development work: prototype design, and validation testing. In prototype development, the mechanical and electrical teams collaborate to design, build and test the physical components of the system, and undergo design reviews from the rest of the team. Likewise, during validation testing, systems are assessed from a manufacturability and performance stand point both separately and as a fully integrated unit. Once a fully integrated unit is tested, construction on a new eet may begin. This has been the case for the current year with the development of the 2013 prototype. Much of the winter semester was spent on discussing changes to, and the designing of the a new system. While the later spring semester contains the actual testing and machining duties.",
    "questions": [
      "What are the main phases of development work in a typical robotics project?"
    ],
    "tdp_name": {
      "index": 0,
      "league": {
        "league_major": "soccer",
        "league_minor": "smallsize",
        "league_sub": null,
        "name": "soccer_smallsize",
        "name_pretty": "Soccer SmallSize"
      },
      "team_name": {
        "name": "RoboJackets",
        "name_pretty": "RoboJackets"
      },
      "year": 2013
    },
    "title": "1 System and Team Overview"
  },
  {
    "content": "Once the cover is placed on the robot it turns on the white LEDs to illuminate the color blobs and reads out the reflected color from the sensors. The identification works very robustly as there are only four colors to separate. To change the team color of a robot the paper for the central blob can be pulled out towards the covers front. This paper is yellow on one side and blue on the other. It just needs to be flipped. The robot knows it sees the underside of this paper and will identify a yellow team color when it reads out blue and vice versa. With this new system it does not matter any more which cover is at hand. Any cover can be placed on any robot and it will adapt. The color sensors can also sense ambient light conditions. Only when ambient light changes significantly a new identification process is started. Furthermore, this also allows us to detect if a robot currently has a cover or not. This can be used for additional safety features (i.e. only charge the kicker with a cover in place). Currently, we use it to enable our wireless interface on the robot. It is inactive as long as there is no cover. This allows us to switch on a robot and perform tests without interfering with our other robots actively participating in a match. Table 1: Robot Specifications Robot version v2020 Dimension 178 x 148 mm Total weight 2.62 kg Max. ball coverage 19.8 % Locomotion Nanotec DF45L024048-A2, 65 W 2 , Direct Drive Wheel diameter 62 mm Encoder iC-Haus iC-PX2604 + PX01S, 23040 ppr [5] Dribbling motor Moons Industries ECU22048H18-S101, 55 W Dribbling gear 1 : 1 : 1 Dribbling bar diameter 11.5 mm Kicker charge 3600 F @ 240 V (103.68 J) Chip kick distance approx. 3.6 m Straight kick speed max.",
    "questions": [
      "How does the robot's wireless interface work and when is it activated?"
    ],
    "tdp_name": {
      "index": 0,
      "league": {
        "league_major": "soccer",
        "league_minor": "smallsize",
        "league_sub": null,
        "name": "soccer_smallsize",
        "name_pretty": "Soccer SmallSize"
      },
      "team_name": {
        "name": "TIGERs_Mannheim",
        "name_pretty": "TIGERs Mannheim"
      },
      "year": 2022
    },
    "title": "1.2 Pattern Identification System"
  },
  {
    "content": "In the competition at RCAP2021, the problem of the differences between the simulator and the actual robot was remarkable, and there was a situation where the actual robot did not operate as expected. In order to avoid differences in the operating environment of the simulator and the actual robot, we adjusted the data sent from RACOON-AI, so that there were no differences between grSim and the actual robot. By doing so, the RACOON-AI that was running in the simulator can be seamlessly transferred to the real robot environment without changing the code.",
    "questions": [
      "How can differences between simulator and actual robot environments be minimized in robotics competitions?"
    ],
    "tdp_name": {
      "index": 0,
      "league": {
        "league_major": "soccer",
        "league_minor": "smallsize",
        "league_sub": null,
        "name": "soccer_smallsize",
        "name_pretty": "Soccer SmallSize"
      },
      "team_name": {
        "name": "Ri-one",
        "name_pretty": "Ri-one"
      },
      "year": 2022
    },
    "title": "4.2.2 Maintaining Compatibility With the Simulator"
  },
  {
    "content": "Robot software development usually requires a full functional real robot, however due to the hardware problems, which experimental robots always suffer from, it's hard to design software during hardware development process. In addition, when a full functional real robot exists, constraints like cost, maximum operation time and possible damages slow down the software development process. Robot simulators can overcome such problems. According to these problems, we use grSim to simulate the SSL games. grSim is a multi-robot simulation environment designed especially for RoboCup small size soccer robot domain. It is able to completely simulate and visualize a robot soccer game with full details. Teams can communicate with the simulator in the same way they communicate with real world, except the commands should be sent to the simulator via network instead of radio connections to the robots [3]. 5 Conclusion In this paper, we presented the last improvements of KN2C SSL team. We tried to cover all of details as many as possible, and also decided to publish all of our projects under an open source license, GPL3. So you can find all of our software, PCB designs and everything in this address: https://www.github.com/kn2cssl We will be appreciate if we can help any of SSL community members, so every questions is welcomed.",
    "questions": [
      "What constraints can slow down the software development process for robot teams?"
    ],
    "tdp_name": {
      "index": 0,
      "league": {
        "league_major": "soccer",
        "league_minor": "smallsize",
        "league_sub": null,
        "name": "soccer_smallsize",
        "name_pretty": "Soccer SmallSize"
      },
      "team_name": {
        "name": "KN2C",
        "name_pretty": "KN2C"
      },
      "year": 2015
    },
    "title": "4.5 Simulation"
  },
  {
    "content": "The main microcomputer receives commands from team AI computer via IEEE 802.15.4 wireless communication module (Digi International, XBee S1) and calculates motor rotation speeds to . The main microcomputer sends the rotation speeds to motor drives via I 2 C communication line. The motor driver consists of a one-chip microcomputer (Microchip, dsPIC33FJ12MC202), a gate driver (Microchip, MCP14700), a three-phase H-bridge driver with six MOSFETs (Diodes Inc., DMG4822SSD), and a rotary encoder (US Digital, E8P). We adopted Maxon EC45 flat motors (1) and reduction gear of 35:80 ratio for driving the wheels. The EC45 motor has a built-in hole sensor to detect the rotor angle and to synchronize the PWM pulse to the angle. The sensor resolution of 48 pulses per round is not adequate for control at the minimum speed of 100 millimeters per second. We add a magnetic rotary encoder of 1440 pulses per round. The microcomputer generates a three-phase PWM pulse at a control interval of 20 milliseconds. We adopt the torque/duty converter technique (2) (Fig. 4). The PI controller calculates the output torque at time k , from the desired angular velocity and motor angular velocity . (3) 1 (4) Where is the angular velocity error at time k , is the proportional gain and is the integral gain. Both gains are settled experimentally. The duty ratio of PWM pulse is, (5) where is the battery voltage (11.1 V), is the motor coil resistance, is the motor torque constant, is the motor speed constant. These values are indicated in the data sheet. 2.2 Robot Speed Control Figure 4 shows the speed control sequence of our robot. At the start, the AI sends a start speed value SP 0 to robots. We normally set SP 0 value to 1.2 meter per second, but decreased to 0.8 or 1.0 meter per second on slippery fields. The AI keeps the speed value constant during five control cycles of waiting for the acceleration of the robot. We set the maximum speed of the robot SP max to 3.0 meters per second experimentally. When the robot approaches the target position, the AI limits SP max from the distance between the robot and the target position for not to overpass the goal.",
    "questions": [
      "How does the robot's speed control sequence work?"
    ],
    "tdp_name": {
      "index": 0,
      "league": {
        "league_major": "soccer",
        "league_minor": "smallsize",
        "league_sub": null,
        "name": "soccer_smallsize",
        "name_pretty": "Soccer SmallSize"
      },
      "team_name": {
        "name": "MCT_Susano_Logics",
        "name_pretty": "MCT Susano Logics"
      },
      "year": 2019
    },
    "title": "2.1 Low Level Controller of MCT Susano Logics Robot"
  },
  {
    "content": "The new hardware design and the new low level motion controller have implemented and they improved the speed, precision, and flexibility of the robots. With some filters, we could acquire precisely coordinates of all players. The modified robot kinematics is used in the simulator and in the real robot. It can improve the robot overall efficiency. We believe that the RoboCup Small-Size League is and will continue to be an excellent domain to drive research on high-performance real-time autonomous robotics. We hope that our robot performs better in this competition than the last year competition. We are looking forward to share experiences with other great teams around the world.",
    "questions": [
      "How can improvements in hardware design and motion controllers impact the performance of robots in autonomous robotics competitions?"
    ],
    "tdp_name": {
      "index": 0,
      "league": {
        "league_major": "soccer",
        "league_minor": "smallsize",
        "league_sub": null,
        "name": "soccer_smallsize",
        "name_pretty": "Soccer SmallSize"
      },
      "team_name": {
        "name": "Skuba",
        "name_pretty": "Skuba"
      },
      "year": 2009
    },
    "title": "7 Conclusion"
  },
  {
    "content": "RCT robot software architecture is described at Fig. 3. Our robots no longer use a base station, each one acting as an autonomous player, even for decision tasks. Code is divided in 2 parts corresponding to the 2 main electronics parts : Code is written in C for the motor and sensor control board based on a Microchip DSP 16-bits controller. For the cortex part embedded on the computer, code is fully written in C #. It is a fully event driven code with more than 60 independent modules linked together like a Matlab Simulink model. This way of coding allows students to work on small parts of the robot without having to know most of the code. It also allows to use the modules in multiple configurations such as the robot itself, or a simulator for the whole team and another opponent team (Fig. ?? ). This method allows to increase the reliability of each module.",
    "questions": [
      "How is the robot software architecture structured to allow students to work on small parts of the robot without having to know most of the code?"
    ],
    "tdp_name": {
      "index": 0,
      "league": {
        "league_major": "soccer",
        "league_minor": "midsize",
        "league_sub": null,
        "name": "soccer_midsize",
        "name_pretty": "Soccer MidSize"
      },
      "team_name": {
        "name": "RCT",
        "name_pretty": "RCT"
      },
      "year": 2023
    },
    "title": "2.2 Software architecture"
  },
  {
    "content": "Using an adaptation of CAMBADAs RTDB [7] for the real-time database, the robot-torobot communication has been implemented. Information gathered by each robot as its pose, obstacles, best ball candidate, intentions and actions etc, are shared through this real-time database, being merged by MinhoTeams base station and shared with every robot, being this information the best information possible, yielding the best perception of the world. The information gathered by every robot has the biggest local importance (inside an area around the robot, in the world model[8]) and the merged information provides data that the robot couldnt know about without information sharing, making possible to make long passes, ball interceptions and other difficult actions, that would be hard with little information. The identification of friend-or-foe is only possible with the information sharing, were one can know which obstacles are teammates, which obstacles are not. This is one of the most important parts of the robot intelligence, allowing information sharing, building the best world model possible, therefore, providing a superior level of robot intelligence.",
    "questions": [
      "What role does real-time database communication play in enhancing the performance of robots in a robotic team?"
    ],
    "tdp_name": {
      "index": 0,
      "league": {
        "league_major": "soccer",
        "league_minor": "midsize",
        "league_sub": null,
        "name": "soccer_midsize",
        "name_pretty": "Soccer MidSize"
      },
      "team_name": {
        "name": "Minho",
        "name_pretty": "Minho"
      },
      "year": 2016
    },
    "title": "6 World Modelling and Communications"
  },
  {
    "content": "Initially, our equipment consists of eight identical robots built in 2011. The mechanical design of these robots won't be significantly changed. The robot measures are 178 mm in diameter and 145 mm high. The driving system (dribbler) covers the ball by 18%, complying with the competition rules. The real robot is showed at Fig. 1.",
    "questions": [],
    "tdp_name": {
      "index": 0,
      "league": {
        "league_major": "soccer",
        "league_minor": "smallsize",
        "league_sub": null,
        "name": "soccer_smallsize",
        "name_pretty": "Soccer SmallSize"
      },
      "team_name": {
        "name": "STOxs",
        "name_pretty": "STOxs"
      },
      "year": 2013
    },
    "title": "2 HARDWARE DESING"
  },
  {
    "content": "Ichiro KidSize robot hardware consists of three main parts, the input device (sensor), processing device, and output device. The input device is used to retrieve data in the robot environment, then the data is processed by the processing device, then the results of the process are used to regulate the output device so that the robot can move correctly. The input device used several types of devices to obtain orientation data, accelerometer, gyroscope, vision, and interfacing for the robot to run the program. Because Fig. 1. Block diagram electronic system of Ichiro Robot of the rules, since 2018 we did not use any compass. We use MPU6050 for the orientation of the robot, whereas the CM-740 build-in IMU sensor are used as the accelerometer and gyroscope. For our vision system a Logitech C920 webcam is used to capture the images, then process them to detect the balls, fields, and goal which are combined with the orientation sensor as the robot heading. The processing device is divided into two types, the main controller and sub-controller. For the main controller, Intel NUC is used. The combination of CM-740 and Arduino nano is utilized for the sub-controller. At the output device, servo motors are used to drive the robot mechanics. The robot uses eight pcs of Dynamixel MX-28 for the upper body, and 12 pcs of Dynamixel MX-64 for the legs. The block diagram of the electronic system shown in Fig. 1 .",
    "questions": [
      "How does the processing device work in a humanoid soccer robot?"
    ],
    "tdp_name": {
      "index": 0,
      "league": {
        "league_major": "soccer",
        "league_minor": "humanoid",
        "league_sub": "kid",
        "name": "soccer_humanoid_kid",
        "name_pretty": "Soccer Humanoid Kid"
      },
      "team_name": {
        "name": "Ichiro",
        "name_pretty": "Ichiro"
      },
      "year": 2019
    },
    "title": "2 Electrical Hardware Overview"
  },
  {
    "content": "We are using a two way communication to our robots by the radio module described in 2.6. To simplify the communication we have implemented a small C library which can be used in the C++ strategy application as well as on the radio transceiver itself. It focuses on three aspects: Same source code on strategy computer and robots Small packet sizes to keep latency low Forward compatibility to be able to use robots without reprogramming them after a protocol extension The feedback channel is used to report battery level, light barrier state, and other system information from the robots to the control computer for visualization.",
    "questions": [
      "How does the two way communication between robots and control computer work?"
    ],
    "tdp_name": {
      "index": 0,
      "league": {
        "league_major": "soccer",
        "league_minor": "smallsize",
        "league_sub": null,
        "name": "soccer_smallsize",
        "name_pretty": "Soccer SmallSize"
      },
      "team_name": {
        "name": "ER-Force",
        "name_pretty": "ER-Force"
      },
      "year": 2010
    },
    "title": "3.3 Radio communication"
  },
  {
    "content": "In order to speed up our robot development, we are also developing robot simulation with SIGVerse 5 . SIGVerse is a robotics simulator that can simulate human-inthe-loop human-robot interaction, capable of representing various task scenarios in RoboCup @Home. Refer to Fig. 9, we have developed a virtual Handyman task that resembles the GPSR task in @Home. We develop and improve our gesture detection system in the virtual Interactive Clean Up task for better human gesture recognition. In the virtual human navigation task, we train our robot system to understand the sentence generation in GPSR. We also use the power of simulation system to conduct repetitive robot learning of huge amount of data via crowdsourcing. 5 http://www.sigverse.org/",
    "questions": [
      "How is robot simulation being used to speed up robot development?"
    ],
    "tdp_name": {
      "index": 0,
      "league": {
        "league_major": "athome",
        "league_minor": "social",
        "league_sub": null,
        "name": "athome_social",
        "name_pretty": "@Home Social"
      },
      "team_name": {
        "name": "KameRider",
        "name_pretty": "KameRider"
      },
      "year": 2019
    },
    "title": "4.4 Simulation Development with SIGVerse"
  },
  {
    "content": "Implementation of the Initial Kick state. function S 2 _ initKick () circleKickBall(Robot3, targetPosition, 100); ERRTNavigate2Point(Robot0, targetPosition); logData(); if cnt >= 5 then nextFunc2Run := S3_oneTouchKick; cnt := 0; else if ballIsMoving() then cnt := cnt + 1; In S2_initKick (), Robot #3 tries to aim the targetPosition and kick the ball towards it. Meanwhile, Robot #0 will try to reach the targetPosition . After a few moments when the ball is moving, the FSM will transit to the next state. Table 5. Implementation of the OneTouchKick state. function S 3 _ oneTouchKick () halt(Robot3); oneTouchDirect(Robot0, targetPosition, oppGoalPosition); logData(); if ballIsOut() then if ballInGoal() then successPositions.add(targetPosition); else failPositions.add(targetPosition); nextFunc2Run := S1_setup; round := round + 1; else if ballIsNotMoving() then failPositions.add(targetPosition); nextFunc2Run := S1_setup; round := round + 1; In S3_oneTouchKick (), Robot #3 gets into a halt mode and Robot #0 will wait for the ball to reach it. Once the ball gets fetched by the robot. it will get kicked towards the oppGoalPosition . The state transition will not happen until the ball exits the field or stops moving. When one of the transition conditions happen it will be judged whether the test was a success or a fail according to the position of the ball in relation with the goal. Table 6. Implementation of the Done state. function S 4 _ done () halt(Robot3); halt(Robot0); logData(); logData(successPositions, GREEN); logData(failPositions, RED); In S4_done (), the robots are halted and the results are sent to the visualizer as red and green points. After running the code with 500 rounds in 1 hour and 20 minutes, the results were shown on the visualizer with 142 successful and 358 failed attempts. Fig 7 shows the visualizer at the end of the test. It is now clearly seen which areas have a high possibility in scoring a goal by a one-touch kick under the tested conditions. Finally, it is worth to notice that the test has been performed in a simulation to give a better result in a short amount of time. It is clear that this test has to be made on robots in the real world.",
    "questions": [
      "How can the results of a simulation in soccer robotics be used to improve performance in real-world robot matches?"
    ],
    "tdp_name": {
      "index": 0,
      "league": {
        "league_major": "soccer",
        "league_minor": "smallsize",
        "league_sub": null,
        "name": "soccer_smallsize",
        "name_pretty": "Soccer SmallSize"
      },
      "team_name": {
        "name": "Immortals",
        "name_pretty": "Immortals"
      },
      "year": 2020
    },
    "title": "3.3 Analyzing"
  },
  {
    "content": "MRL Mechatronic Research Laboratory is located in Qazvin Islamic Azad University research and innovation Center Syntech, in which several teams have focused on robotic and AI research and challenges to contribute new technology and to participate in RoboCup competitions annually. MRL-@Work is a team consist of undergraduate and graduate students and an assistance professor as team supervisor. The vision of this team is to design and build a robust intelligent autonomous industrial robot. We have designed a UGV unmanned ground vehicle robot, called AtisBot composed of two distinguished parts; an Omni-directional base[Fig.1] and a 5DOF robotic arm. The arms 1 ) Dr. Vahid Rostami is the Assist. Prof. in Department of Computer engineering, Qazvin Islamic Azad University, Iran, e-mail: Vh_Rostam@QIAU.AC.IR manipulation and the bases navigation have professionally performed in two year passed We are going to work on grasping system, decision making and task scheduling as well as fault toleration of our system in this year.",
    "questions": [
      "What is the vision of MRL-@Work team regarding the design of their autonomous industrial robot?"
    ],
    "tdp_name": {
      "index": 0,
      "league": {
        "league_major": "industrial",
        "league_minor": "atwork",
        "league_sub": null,
        "name": "industrial_atwork",
        "name_pretty": "Industrial @Work"
      },
      "team_name": {
        "name": "MRL",
        "name_pretty": "MRL"
      },
      "year": 2019
    },
    "title": "1 INTRODUCTION"
  },
  {
    "content": "Elaborate design of the electrical system is an essential guarantee for the normal work of robots. By virtue of design of Rhoban team, we have developed and adjusted an electrical control system which is composed of an up-level computer, a low-level controller and a power supply board. The lower controller is designed by integration of three embedded microcontrollers driving different servo buses of servos and an IMU sensor while the camera is connected to up-level computer through USB port. Such simply design ensure effective utilization of the interior space of the robot. Apart from transferring power from the battery to up-level computer and low-level controller, the power supply board acts as a hot plug switch that ensures uninterruptible power supply if the battery needs to be changed when the robot are working.",
    "questions": [
      "How does the design of the electrical system impact the normal work of robots in soccer humanoid competitions?"
    ],
    "tdp_name": {
      "index": 0,
      "league": {
        "league_major": "soccer",
        "league_minor": "humanoid",
        "league_sub": "kid",
        "name": "soccer_humanoid_kid",
        "name_pretty": "Soccer Humanoid Kid"
      },
      "team_name": {
        "name": "SYCU-Legendary",
        "name_pretty": "SYCU-Legendary"
      },
      "year": 2019
    },
    "title": "3.2 Electrical System Configuration"
  },
  {
    "content": "Our robot uses its autonomous navigation capability in a large, unstructured, and human-inhabited environment. The activities learned by our robot were performed spontaneously by many different people who interacted with (or were observed by) the robot, as opposed to the standard methodology of asking study participants to perform certain actions. In contrast to classic computer vision approaches, our system uses both visual and non-visual cues when recognizing the activities of humans that it interacts with [10]. For space, we are limiting the length this list of contributions. Please see our team website and research group pages for more information.",
    "questions": [
      "How does the robot's autonomous navigation capability work in unstructured and human-inhabited environments?"
    ],
    "tdp_name": {
      "index": 0,
      "league": {
        "league_major": "athome",
        "league_minor": "domestic",
        "league_sub": null,
        "name": "athome_domestic",
        "name_pretty": "@Home Domestic"
      },
      "team_name": {
        "name": "Austin_Villa",
        "name_pretty": "Austin Villa"
      },
      "year": 2019
    },
    "title": "4.4 Robot-centric human activity recognition"
  },
  {
    "content": "Our AI application had some problems because of lack of time in 2009. In this year, we are trying to solve the problems like instability in role assigning and motion control for our new robots and AI application. In [2] we described our roles and skills details and relations between them which are inspired from CMU game structure [3], [4]. Also we added a new layer in our hierarchical playing architecture which is inserted between role and skill, called technique. A technique is not a role (the play is constructed based on roles and each strategy utilizes some specified roles with unique arrangement) but it can apply skills to generate new behavior. For example chip dribble is a technique that uses go to point and aim and kick skills. There is a technique matcher to match the feasible technique in all conditions too. Last year a flexible comprehensive software structure was designed but the time was not sufficient for debugging the code especially in practice. Working on robot which never was manufactured so long time before competitions in previous years, aided us to increase their abilities in this year competitions. We hope that more reliability in our software and hardware can improve our performance more than ever.",
    "questions": [
      "How did working on robots that were never manufactured before aid the MRL team in increasing their abilities for the 2010 competitions?"
    ],
    "tdp_name": {
      "index": 0,
      "league": {
        "league_major": "soccer",
        "league_minor": "smallsize",
        "league_sub": null,
        "name": "soccer_smallsize",
        "name_pretty": "Soccer SmallSize"
      },
      "team_name": {
        "name": "MRL",
        "name_pretty": "MRL"
      },
      "year": 2010
    },
    "title": "2.1. AI Console"
  }
]"""

    if query == "cached response":
      logger.info("Returning cached response")
      flask_response = Response(myresponse)
      flask_response.headers['Content-Type'] = "application/json"
      flask_response.headers['Cache-Control'] = "max-age=604800, public"
      return flask_response

    paragraphs, keywords = search(vector_client, query, filter, compress_text=True)
    paragraphs_json = []
    for paragraph in paragraphs:
        paragraphs_json.append({
            'tdp_name': paragraph.tdp_name.to_dict(),
            'title': paragraph.text_raw,
            'content': paragraph.content_raw(),
            'questions': paragraph.questions,
        })

    result = {
        'paragraphs': paragraphs_json,
        'keywords': keywords
    }    

    flask_response = Response(json.dumps(result))
    flask_response.headers['Content-Type'] = "application/json"
    # flask_response.headers['Cache-Control'] = "max-age=604800, public"
    return flask_response

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)