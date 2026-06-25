################################################################################
# Automatically-generated file. Do not edit!
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
C_SRCS += \
"../Apps/App_Ultrasonic/App_Ultrasonic.c" 

COMPILED_SRCS += \
"Apps/App_Ultrasonic/App_Ultrasonic.src" 

C_DEPS += \
"./Apps/App_Ultrasonic/App_Ultrasonic.d" 

OBJS += \
"Apps/App_Ultrasonic/App_Ultrasonic.o" 


# Each subdirectory must supply rules for building sources it contributes
"Apps/App_Ultrasonic/App_Ultrasonic.src":"../Apps/App_Ultrasonic/App_Ultrasonic.c" "Apps/App_Ultrasonic/subdir.mk"
	cctc -cs --dep-file="$*.d" --misrac-version=2012 -D__CPU__=tc37x "-fC:/Users/starryeev/Documents/Projects/AURIX Development Studio/sensor-ecu/TriCore Debug (TASKING)/TASKING_C_C___Compiler-Include_paths__-I_.opt" --iso=99 --c++14 --language=+volatile --exceptions --anachronisms --fp-model=3 -O0 --tradeoff=4 --compact-max-size=200 -g -Wc-w544 -Wc-w557 -Ctc37x -Y0 -N0 -Z0 -o "$@" "$<"
"Apps/App_Ultrasonic/App_Ultrasonic.o":"Apps/App_Ultrasonic/App_Ultrasonic.src" "Apps/App_Ultrasonic/subdir.mk"
	astc -Og -Os --no-warnings= --error-limit=42 -o  "$@" "$<"

clean: clean-Apps-2f-App_Ultrasonic

clean-Apps-2f-App_Ultrasonic:
	-$(RM) ./Apps/App_Ultrasonic/App_Ultrasonic.d ./Apps/App_Ultrasonic/App_Ultrasonic.o ./Apps/App_Ultrasonic/App_Ultrasonic.src

.PHONY: clean-Apps-2f-App_Ultrasonic

