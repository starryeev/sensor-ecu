################################################################################
# Automatically-generated file. Do not edit!
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
C_SRCS += \
"../Drivers/Can/McmcanFd.c" 

COMPILED_SRCS += \
"Drivers/Can/McmcanFd.src" 

C_DEPS += \
"./Drivers/Can/McmcanFd.d" 

OBJS += \
"Drivers/Can/McmcanFd.o" 


# Each subdirectory must supply rules for building sources it contributes
"Drivers/Can/McmcanFd.src":"../Drivers/Can/McmcanFd.c" "Drivers/Can/subdir.mk"
	cctc -cs --dep-file="$*.d" --misrac-version=2012 -D__CPU__=tc37x "-fC:/Users/starryeev/Documents/Projects/AURIX Development Studio/sensor-ecu/TriCore Debug (TASKING)/TASKING_C_C___Compiler-Include_paths__-I_.opt" --iso=99 --c++14 --language=+volatile --exceptions --anachronisms --fp-model=3 -O0 --tradeoff=4 --compact-max-size=200 -g -Wc-w544 -Wc-w557 -Ctc37x -Y0 -N0 -Z0 -o "$@" "$<"
"Drivers/Can/McmcanFd.o":"Drivers/Can/McmcanFd.src" "Drivers/Can/subdir.mk"
	astc -Og -Os --no-warnings= --error-limit=42 -o  "$@" "$<"

clean: clean-Drivers-2f-Can

clean-Drivers-2f-Can:
	-$(RM) ./Drivers/Can/McmcanFd.d ./Drivers/Can/McmcanFd.o ./Drivers/Can/McmcanFd.src

.PHONY: clean-Drivers-2f-Can

