test_cases_paragraphs = {
    "./TDPs/2015/2015_TDP_Warthog_Robotics.pdf": ['1 Introduction', '2 Mechanical Structure', '3 Electronic Devices', '3.1 MainBoard', '3.2 MotorBoard', '3.3 KickBoard', '4 Compuer Systems', '4.1 GEARSystem', '4.2 WRCoach', '5 Improvements for 2015', '6 Conclusion and Future Work', '7 Acknowledgments'],
    "./TDPs/2015/2015_TDP_ACES.pdf": ['1 Robot Specifications:', '2 Electrical System:', '2.1 Current Electrical Architecture:', '2.2 Motor Drives:', '2.3 Central Processing Unit:', '2.4 Previous Electrical Problems & Solutions:', '2.4.1 NRF905 Wireless Transceiver Module:', '2.4.2 Encoders feedback and Motion Control:', '2.4.3 Kicker Redesign:', '3 Mechanical System:', '3.1 New Mechanical additions:', '3.2 Previous Mechanical Problems & Solutions:', '3.2.1 Main circuit board connector:', '3.2.2 Jerk absorbers for kicker jerks:', '4 Software', '4.1 Game Control engine:', '4.2 Improved Motion Control:', '4.3 Path Planning:'],
    "./TDPs/2022/2022_ETDP_RoboTeam_Twente.pdf": ['1 Introduction', '2 General Part Hardware', '3 Modifications of Mechanics', '3.1 Redesign of the front assembly', '3.2 Redesign of the top assembly', '3.3 Design of Custom Solenoids', '4 Modifications of Electronics', '4.1 Kicker and Chipper Module', '4.2 Dribbler Module', '4.3 Power Module', '4.4 Other Improvements'],
    "./TDPs/2014/2014_ETDP_CMDragons.pdf": ['1 Introduction', '2 The Robots and Basic Skills', '3 Passing', '3.1 Pass Location Selection', '3.2 Pass-ahead Coordination', '4 Human Coaching', '4.1 Gaussian Naive Bayes', '4.2 Support Vector Machine', '4.3 Comparison', '4.4 Model Plus Correction', '5 The Coerce And Attack Planner', '5.1 Tactic Detection', '5.2 Computing Attack Plans', '5.3 Computing The Coerce Plan', '6 Threat-Based Defense', '6.1 First-level Threat', '6.2 Second-level Threats', '7 Performance', '8 Conclusion'],
    "./TDPs/2015/2015_TDP_KN2C.pdf": ['1 Introduction', '2 Electronics', '2.1 Main Board', '2.2 Motor Drivers', '2.3 Wireless communication', '2.4 Kick Circuit', '3 Mechanics', '4 Software', '4.1 Navigation', '4.2 Offensive Positioning', '4.3 Control', '4.4 User Interface', '4.5 Simulation', '5 Conclusion'],
    "./TDPs/2015/2015_ETDP_RoboDragons.pdf": ['1 Introduction', '2 Robot Hardware', '2.1 Improvement of Radio System', '2.2 Improvement around Dribble Device', '3 Dynamic Ball Kicking', '3.1 Design of a motion profile for the velocity V', '3.2 Design of a motion profile for the velocity V', '4 Circle-and-Pass Skill on Throw-in', '4.1 Algorithm', '4.2 Comparisons', '5 Concluding Remarks'],
    "./TDPs/2014/2014_ETDP_KIKS.pdf": ['1. Introduction', '2. Hardware of the robot', '3. Electrical design', '3.1 Specification of MCU', '3.2 New system in FPGA', '3.3 Motor Driver of Base Board', '3.4 New PC Software for circuit', '3.5 Inertial Measurement Unit for base board', '3.6 Evaluation of IMU', '4. Software design', '4.1. Improvement of the structure of strategy system', '4.2. About controller of Robot', '5. Conclusions'],
}

# Exception make for KN2C 2015. 'Figure 4 Motor Drivers .' should be 'Figure 4. Motor Drivers', but that is such a weird unparsable sentence.. Don't even try
test_cases_figure_descriptions = {
    "./TDPs/2015/2015_TDP_Warthog_Robotics.pdf": ['Fig. 1. Internal mechanical assembly of the 2015 Warthog Robotics SSL robot.', 'Fig. 2. Block diagram of the embedded electronic systems of the 2015 Warthog Robotics SSL robot.', 'Fig. 3. Conceptual diagram of the modules of the WRCoach software.'],
    "./TDPs/2015/2015_TDP_ACES.pdf": ['Figure 1: Block diagram of our motor drive control.', 'Figure 1: Block diagram of our motor drive control.', 'Figure 2: Graph of our PWM and Current Analysis', 'Figure 3: Image of NRF905 Wireless Module [1].', 'Figure 4: Figure of Complete Drive Control', 'Figure 5: Figure of Feedback control of Motors', 'Figure 7: Figure of Kicker Simulation', 'Figure 8: 3D Design of Complete wheel assembly and Chasses.', 'Figure 8: 3D Design of Complete wheel assembly and Chasses.', 'Figure 9: 3D Design of Kicker with Rubber Washers at both ends.', 'Figure 10: Complete AI flow chart', 'Figure 11: Node Skipping Methodology for path smoothing', 'Figure 11: Node Skipping Methodology for path smoothing'],
    "./TDPs/2022/2022_ETDP_RoboTeam_Twente.pdf": ['Fig. 1. Side view of the 2021 version of the robot', 'Fig. 2. Overview of the desired modules for the modular design', 'Fig. 3. Schematic overview of the test setup', 'Fig. 4. Graphs of the damping test with the poor dampening (left) and reasonably dampening (right). Note that the vertical axes have different scales.', 'Fig. 4. Graphs of the damping test with the poor dampening (left) and reasonably dampening (right). Note that the vertical axes have different scales.', 'Fig. 5. Render of the proposed redesign of the front assembly', 'Fig. 6. Section view of the proposed design of the front assembly', 'Fig. 7. Renders of the old (left) and new (right) top plates.', 'Fig. 7. Renders of the old (left) and new (right) top plates.', 'Fig. 8. Renders of the old (left) and new (right) back PCB holders.', 'Fig. 8. Renders of the old (left) and new (right) back PCB holders.', 'Fig. 9. Render of the proposed design of a custom solenoid', 'Fig. 10. Rolling motion of the ball', 'Fig. 11. FEMM model of solenoid', 'Fig. 12. Solution with varying flux density', 'Fig. 13. Magnetic flux', 'Fig. 14. Electronics modular design plan', 'Fig. 15. Comparison between 3.3 LDO and power converter'],
    "./TDPs/2014/2014_ETDP_CMDragons.pdf": ['Fig. 1. The CMDragons robots, showing (left) a robot with the ball, (middle) without the cover, and (right) without the electronic main board.', 'Fig. 2. The estimated probability that a pass from the ball location (orange circle) will not be intercepted. This probability is high for locations with ball trajectories that pass far from opponents, such as a , and low for those with ball trajectories that pass close, such as b . Some passes, such as c , pass close to the opponent but can still be successful using chip passes, although the prior success probability for those is lower than for regular passes, as indicated by the gray region to the right.', 'Fig. 3. The estimated probability that a given location x has a wide enough open angle on the opponents goal (blue line) to score a goal. The left image shows a location with a wide open angle, ideal for a shot. The right image shows two locations with relatively small open angles, one due to obstruction by a robot and distance from the goal, and the other because of its location near the corner of the field.', 'Fig. 3. The estimated probability that a given location x has a wide enough open angle on the opponents goal (blue line) to score a goal. The left image shows a location with a wide open angle, ideal for a shot. The right image shows two locations with relatively small open angles, one due to obstruction by a robot and distance from the goal, and the other because of its location near the corner of the field.', 'Fig. 5. A passing evaluation function is overlaid on top of the field in greyscale. Whiter values signify high-value locations. Values in black are less than 0 . 5% of the optimal value. The red square represents the optimal location chosen by the human coach.', 'Fig. 6. The probability distributions given by the models for various tactics opponent robots might run, including Mark (red), Wall (purple), Primary Defender (green), and Goalkeeper (blue). The defense area line is shown in white, our robots in yellow, and the ball in orange.'],
    "./TDPs/2015/2015_TDP_KN2C.pdf": ['Figure 1. Our Robots', 'Figure 2. Block diagram of the electrical system.', 'Figure 3. Main Board', 'Figure 4 Motor Drivers .', 'Figure 5. Wireless Board', 'Figure 6. Boost Circuit', 'Figure 7. Kicker Board', 'Figure 8. 3D figure of the robot wheel', 'Figure 9. Direct kick system', 'Figure 10. Overview of Software System', 'Figure 11. Neighbor nodes are shown in blue dots. The output of A* algorithm is presented with red color.', 'Figure 12. Output of Voronoi diagram, blue team are attacking.', 'Figure 13. PID controller vs PD core controller with CTS', 'Figure 14. Diversion in direction of displacement', 'Figure 15. Goal chances visualization'],
    "./TDPs/2015/2015_ETDP_RoboDragons.pdf": ['Fig. 1. Current robot developed in 2012 (modified in 2015)', 'Fig. 1. Current robot developed in 2012 (modified in 2015)', 'Fig. 2. Components of the robot', 'Fig. 2. Components of the robot', 'Fig. 2. Components of the robot', 'Fig. 2. Components of the robot', 'Fig. 2. Components of the robot', 'Fig. 2. Components of the robot', 'Fig. 2. Components of the robot', 'Fig. 3. Laterally projected drawing of the chip-kick board', 'Fig. 3. Laterally projected drawing of the chip-kick board', 'Fig. 4. Experimental results of flying distance in chip-kicking', 'Fig. 5. Geometric relation between robot and ball in dynamic ball kicking.', 'Fig. 9. Computation of P based on the velocity profile (Step 3)', 'Fig. 10. Computation of P based on the velocity profile (Step 5)'],
}

test_cases_pagenumbers = {
    "./TDPs/2015/2015_TDP_Warthog_Robotics.pdf": ['2', 'Warthog Robotics', 'Description of the Warthog Robotics SSL 2015 Project', '3', '4', 'Warthog Robotics', 'Description of the Warthog Robotics SSL 2015 Project', '5', '6', 'Warthog Robotics', 'Description of the Warthog Robotics SSL 2015 Project', '7'],
    "./TDPs/2015/2015_TDP_ACES.pdf": [],
    "./TDPs/2022/2022_ETDP_RoboTeam_Twente.pdf": ['2', 'RoboTeam Twente', 'RoboTeam Twente Extended Team Description Paper for RoboCup 2022', '3', '4', 'RoboTeam Twente', 'RoboTeam Twente Extended Team Description Paper for RoboCup 2022', '5', '6', 'RoboTeam Twente', 'RoboTeam Twente Extended Team Description Paper for RoboCup 2022', '7', '8', 'RoboTeam Twente', 'RoboTeam Twente Extended Team Description Paper for RoboCup 2022', '9', '10', 'RoboTeam Twente', 'RoboTeam Twente Extended Team Description Paper for RoboCup 2022', '11', '12', 'RoboTeam Twente', 'RoboTeam Twente Extended Team Description Paper for RoboCup 2022', '13', '14', 'RoboTeam Twente', 'RoboTeam Twente Extended Team Description Paper for RoboCup 2022', '15', '16', 'RoboTeam Twente'],
    "./TDPs/2014/2014_ETDP_CMDragons.pdf": ['2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16', '17'],
    "./TDPs/2015/2015_TDP_KN2C.pdf": [],
    "./TDPs/2015/2015_ETDP_RoboDragons.pdf": ['2', 'Y. Adachi, H. Kusakabe, Y. Yamanaka, M. Ito, K. Murakami, and T. Naruse', 'RoboDragons 2015 Extended Team Description', '3', '4', 'Y. Adachi, H. Kusakabe, Y. Yamanaka, M. Ito, K. Murakami, and T. Naruse', 'RoboDragons 2015 Extended Team Description', '5', '6', 'Y. Adachi, H. Kusakabe, Y. Yamanaka, M. Ito, K. Murakami, and T. Naruse', 'RoboDragons 2015 Extended Team Description', '7', '8', 'Y. Adachi, H. Kusakabe, Y. Yamanaka, M. Ito, K. Murakami, and T. Naruse', 'RoboDragons 2015 Extended Team Description', '9', '10', 'Y. Adachi, H. Kusakabe, Y. Yamanaka, M. Ito, K. Murakami, and T. Naruse', 'RoboDragons 2015 Extended Team Description', '11'],
}

""" Regression tests to ensure that changes to the code do not break the output of the code """

def test_paragraph_titles(tdp, paragraph_titles):
    # Return True by default
    if tdp not in fill_database_tests.test_cases_paragraphs: return True
    
    titles = []
    for sentences in paragraph_titles:
        titles.append(" ".join([ _['text'] for _ in sentences ]))
    if fill_database_tests.test_cases_paragraphs[tdp] != titles:
        for a, b in zip(fill_database_tests.test_cases_paragraphs[tdp], titles):
            if a != b:
                print("Error!")
                print(f"|{a}|")
                print(f"|{b}|")
        raise Exception(f"Test case paragraphs failed for {tdp}!")

def test_image_description(tdp, images):
    # Return True by default
    if tdp not in fill_database_tests.test_cases_figure_descriptions: return True

    image_descriptions = [ _['description'] for _ in images ]
    if fill_database_tests.test_cases_figure_descriptions[tdp] != image_descriptions:
        for a, b in zip(fill_database_tests.test_cases_figure_descriptions[tdp], image_descriptions):
            if a != b:
                print("Error!")
                print(a)
                print(b)
        raise Exception(f"Test case figure descriptions failed for {tdp}!")       

def test_pagenumbers(tdp, pagenumber_sentences):
    if tdp not in fill_database_tests.test_cases_pagenumbers: return True
    text_pagenumbers = [ _['text'] for _ in pagenumber_sentences ]
    if fill_database_tests.test_cases_pagenumbers[tdp] != text_pagenumbers:
        raise Exception(f"Test case pagenumbers failed for {tdp}!")
