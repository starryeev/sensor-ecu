#ifndef __APP_ULTRASONIC_H__
#define __APP_ULTRASONIC_H__

#include "Ifx_Types.h"
#include "IfxPort_PinMap.h"

//#define ULTRASONIC_SENSOR_NUM   (10)


void UltrasonicApp_Init(void);
void UltrasonicApp_Run(void);
//void UltrasonicApp_GetDistanceMmList(uint16_t* outputList, uint8 len);


#endif
