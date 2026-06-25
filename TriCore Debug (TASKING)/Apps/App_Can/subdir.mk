################################################################################
# Automatically-generated file. Do not edit!
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
C_SRCS += \
"../Apps/App_Can/App_Can.c" 

COMPILED_SRCS += \
"Apps/App_Can/App_Can.src" 

C_DEPS += \
"./Apps/App_Can/App_Can.d" 

OBJS += \
"Apps/App_Can/App_Can.o" 


# Each subdirectory must supply rules for building sources it contributes
"Apps/App_Can/App_Can.src":"../Apps/App_Can/App_Can.c" "Apps/App_Can/subdir.mk"
	cctc -cs --dep-file="$*.d" --misrac-version=2012 -D__CPU__=tc37x "-fC:/Users/starryeev/Documents/Projects/AURIX Development Studio/sensor-ecu/TriCore Debug (TASKING)/TASKING_C_C___Compiler-Include_paths__-I_.opt" --iso=99 --c++14 --language=+volatile --exceptions --anachronisms --fp-model=3 -O0 --tradeoff=4 --compact-max-size=200 -g -Wc-w544 -Wc-w557 -Ctc37x -Y0 -N0 -Z0 -o "$@" "$<"
"Apps/App_Can/App_Can.o":"Apps/App_Can/App_Can.src" "Apps/App_Can/subdir.mk"
	astc -Og -Os --no-warnings= --error-limit=42 -o  "$@" "$<"

clean: clean-Apps-2f-App_Can

clean-Apps-2f-App_Can:
	-$(RM) ./Apps/App_Can/App_Can.d ./Apps/App_Can/App_Can.o ./Apps/App_Can/App_Can.src

.PHONY: clean-Apps-2f-App_Can

