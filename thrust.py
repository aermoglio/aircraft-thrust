import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

plt.rcParams.update({
    "text.usetex": True,
    "font.family": "serif",
    "font.serif": ["Computer Modern Roman"],
    "font.size":12,
})

#reading the data
filename="data/airplane.csv"

df=pd.read_csv(filename)

#defining variables
rho_0 = 1.225   #kg/m3 air density at sea level
rho_11 = 0.364    #kg/m3 air density at h=11000
g = 9.81        # m/s^2 acceleration due to gravity
R = 287.05      # ispecific gas constant , for dry air
L = 0.0065       # K/m , temperature lapse rate, how air temp changes with height
h_11 = 11000      # m,  height at 11000 m
T0 =  288.15      # K, temperature at ground level
T11 = T0-L*h_11   # temperature at h=11000 m
gamma=1.4         #adiabatic index for air
e=0.8            #efficiency, approx

#defining functions -----------------------------------------------------------------------
def wing_load (weight,wing_area):    #wing load
    return (weight/wing_area)

def speed_sound (h):                # speed of sound as a function of altitude. this is needed to calculate mach
    if h<=11000:
        T=T0-L*h
    elif h>11000:
        T=T11      #ISOTHERMAL layer
    return (np.sqrt(gamma*R*T))

def wing_aspect_r (wing_area,wing_span):    #wing aspect ratio
    return ((wing_span)**2)/wing_area

def air_density(h):                 #air density
    if h<=11000:
        rho=rho_0*(1-(L*h/T0))**((g/(R*L))-1)
    elif h>11000 and h<=20000:
        rho=rho_11*np.exp(-g*(h-h_11)/(R*T11))
    return rho

def cl(mass,rho,v,wing_area):          #lift coefficient
    cl=2*mass*g/(rho*wing_area*v**2)
    return cl

def C_di(cl,aspect_r):          #coefficient of induced drag
    cdi=(cl**2)/(np.pi*aspect_r*e)
    return cdi

def cd(cdi,cdp):           #total drag coefficient
    cd=cdi+cdp
    return cd

def thrust_req(rho,v,wing_area,C_d):
    thrust_req=0.5*rho*(v**2)*wing_area*C_d
    return thrust_req

#------------------------------------------END FUNCTIONS---------------------------------------------------------

# programme ---------------------------------------------------------------------------------------------------------

#data extraction from file 
models=list(df["Model"])   #i have made the models into a list to use later 

heights=[5000,8000,11000,15000,18000]
v=np.linspace(50,800,750)

results={}                #creating dictionary to store results for each height
wing_loads=[]             # empty list to store wing load data

for i,item in enumerate(models):                    #loop over each model to calculate for each
    row=df[df["Model"]==item]    #separating each model

    results[item]={}                       #dictionary within a dictionary to store each height data for each model
    #extracting variables
    wing_area=float(row["Wing area"].values[0])       #had to convert from a series to a scalar using.values
    wing_span=float(row["Wing span"].values[0])
    mass=float(row["mass"].values[0])
    C_dp=float(row["C_dp"].values[0])

    wing_load_val=mass*g/wing_area
    wing_loads.append(wing_load_val)

    for j,h in enumerate(heights):                      #loop over each height to calculate values for each height
        rho=air_density(h)
        coeff_l=cl(mass,rho,v,wing_area)           #will determine coefficients at all speeds

        aspect_ratio=wing_aspect_r(wing_area,wing_span)
        coeff_di=C_di(coeff_l,aspect_ratio)
        coeff_d=cd(coeff_di,C_dp)
        
        thrust=thrust_req(rho,v,wing_area,coeff_d)
        thrust = thrust.flatten()
        results[item][f"h{j+1}"] = thrust          #adding results to our dictionary


#to calculate mach at different altitudes, we need the speed of sound at different altitudes
#we can do this using our speed of sound function

machs_heights={}                           #dictionary storing the mach values for each height

for i,h in enumerate(heights):
    sound_v=speed_sound(h)
    mach_v=v/sound_v
    machs_heights[f"h{i+1}"]=mach_v

#now that we have the data, we can plot the results

# PLOTTING!
#--------------------------------------------------------------------------------------------------
#FIRST PLOT: Wing load for each plane (bar plot)

fig,ax=plt.subplots()

ax.bar(np.arange(1,4),wing_loads, color="coral")

ax.set_xticks(np.arange(1,4))
ax.set_xticklabels(models)

ax.set_xlabel("Model")
ax.set_ylabel("Wing load (N/m$^2$)")

#-------------------------------------------------------------------------------------------------------

#SECOND PLOT: Thrust required vs airspeed, with minimum drag velocity denoted on graph

min_dragv={}                         #create empty dictionary to store the data. dictionaries are a great way to store data

for model in models:
    plt.figure()
    min_drag_list=[]                 #list that will store data for each aircraft. this data is then stored in a dictionary
    for h,item in zip(heights,results[model].items()):
        plt.plot(v*3.6,item[1]/1000,linewidth=2,label=f"{h/1000}")  
        minimum_idx=(item[1]/1000).argmin()
        min_drag_list.append(v[minimum_idx]*3.6)
        min_dragv[model]=min_drag_list

    plt.legend(title="Height (km)",loc="upper right")
    plt.title(f"{model}")
    plt.xlabel("Velocity (km/h)")
    plt.ylabel("Thrust Required (kN)")
    plt.ylim(0,400)

plt.show()
#--------------------------------------------------------------------------------
#THIRD PLOT: Minimum drag airspeed vs height, with line fit

plt.figure(figsize=(5,8))

markers=["o","^","s"]
colors=["tab:blue","tab:orange","tab:green"]

def exponential(x, A, a, C,m, lambda_):
    return A*a**((x-m)*lambda_)+C

# fitting minimum drag airspeed data using scipy.optimize
points=np.linspace(0,18,200)
initial_guesses=[1,5,500,0,0.5]

for model,marker,color in zip(models,markers,colors):
    plt.scatter(np.array(heights)/1000,min_dragv[model], marker=marker, alpha=0.7, label=f"{model}")           # minimum drag airspeed v vs height
    params,params_covariance=curve_fit(exponential, np.array(heights)/1000, min_dragv[model], p0=initial_guesses)
    plt.plot(points, exponential(points, *params), color=color,alpha=0.7,linestyle="--", label=f"{model} Fit")


plt.xlabel("Height (km)")
plt.ylabel("Minimum drag airspeed(km/h)")

plt.legend()

plt.show()

#--------------------------------------------------------------------------------------------------------

#FOURTH PLOT: Thrust required vs mach number, with reported cruise Mach marked (assuming Mach hold!)

for model in models:                #creating a loop to avoid redundancy
    plt.figure()
    for i,h in enumerate(heights):
        selected_mach = machs_heights[f"h{i+1}"]
        plt.plot(selected_mach, results[model][f"h{i+1}"]/1000, label=f"{h/1000} km")
    
    mach_cruise = df[df["Model"] == model]["Mach cruise"].iloc[0]
    plt.axvline(mach_cruise, color="grey", linestyle="--", label="Cruise Mach")
    
    plt.legend(title="Height (km)", loc="upper right")
    plt.title(model)
    plt.xlabel("Mach")
    plt.ylabel("Thrust Required (kN)")
    plt.xlim(0.6, 1)
    plt.ylim(0, 150)

plt.show()
#---------------------------------------------------------------------------------------------------------

# FIFTH PLOT: Min drag mach vs cruise mach?  , bar plot
#min drag stored in min_dragv dictionary  

#i want a cluster of bars for each altitude. do just one altitude (11000)

fig,ax=plt.subplots()
width=0.2

x = np.arange(len(models))

mach=[]                                    #cruise mach values
mindrag=[] 

for model in models:
    
    mach_cruise = df[df["Model"] == model]["Mach cruise"].iloc[0]
    min_dragv_value=min_dragv[model][2]/(speed_sound(11000) *3.6)     #will give min drag value at height 11000 (index 2) in Mach units
    mach.append(mach_cruise)
    mindrag.append(min_dragv_value)

ax.bar(x-width/2,mach,width,label="Cruise mach")
ax.bar(x+width/2,mindrag,width,label="Min. drag speed")


ax.set_title("Mach cruise speed vs minimum drag speed")
ax.set_xticks(x)
ax.set_xticklabels(models)
ax.set_ylabel("Speed (Mach)")

ax.legend()

plt.show()

