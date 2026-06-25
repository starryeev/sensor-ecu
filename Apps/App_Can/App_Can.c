/**********************************************************************************************************************
 * \file App_Can.c
 *********************************************************************************************************************/

/*********************************************************************************************************************/
/*-----------------------------------------------------Includes------------------------------------------------------*/
/*********************************************************************************************************************/
#include "App_Can.h"

#include "Apps/App_Ultrasonic/App_Ultrasonic.h"
#include "Drivers/Can/McmcanFd.h"

#include "FreeRTOS.h"
#include "task.h"

/*********************************************************************************************************************/
/*------------------------------------------------------Macros-------------------------------------------------------*/
/*********************************************************************************************************************/
#define CAN_APP_SEND_INTERVAL_MS                (100U)

/*********************************************************************************************************************/
/*-------------------------------------------------Global Variables--------------------------------------------------*/
/*********************************************************************************************************************/
static boolean g_isInitialized = FALSE;
static sint16 g_imuYaw = 0;
static uint8  g_vehicleSpeed = 0U;

/*********************************************************************************************************************/
/*------------------------------------------------Function Prototypes------------------------------------------------*/
/*********************************************************************************************************************/
static void sendUltrasonicDistanceMessage(void);

/*********************************************************************************************************************/
/*---------------------------------------------Function Implementations----------------------------------------------*/
/*********************************************************************************************************************/
static void sendUltrasonicDistanceMessage(void)
{
    UltrasonicDistanceCmd_t message;

    message.frontDist = g_distances[0];
    message.frontRightDist = g_distances[1];
    message.rightFrontDist = g_distances[2];
    message.rightBehindDist = g_distances[3];
    message.behindRightDist = g_distances[4];
    message.behindDist = g_distances[5];
    message.behindLeftDist = g_distances[6];
    message.leftBehindDist = g_distances[7];
    message.leftFrontDist = g_distances[8];
    message.frontLeftDist = g_distances[9];
    message.imuYaw = g_imuYaw;
    message.vehicleSpeed = g_vehicleSpeed;

    McmcanFd_SendUltrasonic(&message);
}

void CanApp_Init(void)
{
    if (g_isInitialized == TRUE)
    {
        return;
    }

    McmcanFd_Init();

    g_isInitialized = TRUE;
}

void CanApp_Run(void *arg)
{
    (void)arg;

    CanApp_Init();

    while (1)
    {
        sendUltrasonicDistanceMessage();
        vTaskDelay(pdMS_TO_TICKS(CAN_APP_SEND_INTERVAL_MS));
    }
}

void CanApp_SetImuYaw(sint16 imuYaw)
{
    g_imuYaw = imuYaw;
}

void CanApp_SetVehicleSpeed(uint8 vehicleSpeed)
{
    g_vehicleSpeed = vehicleSpeed;
}
