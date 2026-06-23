#include "App_Ultrasonic.h"
#include "IfxGtm.h"
#include "FreeRTOS.h"
#include "task.h"

#define SONIC_SPEED (343)   // MM PER MS 섭씨20도

#define ULTRASONIC_SENSOR_COUNT (10)
#define ULTRASONIC_INVALID_DISTANCE_MM  (0xFFFF)

#define ULTRASONIC_MIN_DISTANCE_MM  (10u)
#define ULTRASONIC_MAX_DISTANCE_MM  (3000u)


typedef struct {
    Ifx_P* port;
    uint8 pin;

    IfxGtm_Tim tim;
    IfxGtm_Tim_Ch timChannel;
    uint8 timInputSelect;

    uint32 durationUs;
    uint16 distanceMm;
    //status?
} UltrasonicSensor;

typedef enum {
    ULTRASONIC_MEASURE_IDLE = 0,
    ULTRASONIC_MEASURE_TRIGGERING,
    ULTRASONIC_MEASURE_WAIT_RISING,
    ULTRASONIC_MEASURE_WAIT_FALLING,
    ULTRASONIC_MEASURE_DONE,
    ULTRASONIC_MEASURE_ERROR
} UltrasonicMeasureState;


/* static 변수 */
static UltrasonicSensor g_sensors[ULTRASONIC_SENSOR_COUNT] = {
    { &MODULE_P15, 3U, IfxGtm_Tim_3, IfxGtm_Tim_Ch_6, 4U, 0U, ULTRASONIC_INVALID_DISTANCE_MM},
    { &MODULE_P15, 2U, IfxGtm_Tim_3, IfxGtm_Tim_Ch_5, 4U, 0U, ULTRASONIC_INVALID_DISTANCE_MM},
    { &MODULE_P02, 0U, IfxGtm_Tim_0, IfxGtm_Tim_Ch_0, 2U, 0U, ULTRASONIC_INVALID_DISTANCE_MM},
    { &MODULE_P02, 1U, IfxGtm_Tim_0, IfxGtm_Tim_Ch_1, 2U, 0U, ULTRASONIC_INVALID_DISTANCE_MM},
    { &MODULE_P10, 4U, IfxGtm_Tim_0, IfxGtm_Tim_Ch_6, 2U, 0U, ULTRASONIC_INVALID_DISTANCE_MM},
    { &MODULE_P02, 3U, IfxGtm_Tim_0, IfxGtm_Tim_Ch_3, 2U, 0U, ULTRASONIC_INVALID_DISTANCE_MM},
    { &MODULE_P02, 5U, IfxGtm_Tim_0, IfxGtm_Tim_Ch_5, 1U, 0U, ULTRASONIC_INVALID_DISTANCE_MM},
    { &MODULE_P02, 4U, IfxGtm_Tim_0, IfxGtm_Tim_Ch_4, 1U, 0U, ULTRASONIC_INVALID_DISTANCE_MM}
};

static volatile UltrasonicMeasureState g_measureState = ULTRASONIC_MEASURE_IDLE;
static volatile uint8 g_activeSensorIdx = 0xFF;
static volatile uint32 g_echoRiseUs = 0u;
static volatile uint32 g_echoDurationUs = 0u;
static volatile uint16 g_measuredDistanceMm = ULTRASONIC_INVALID_DISTANCE_MM;

static TaskHandle_t g_waitingTaskHandle = NULL;
static boolean g_isInitializd = FALSE;


/* 인터럽트 선언 */
IFX_INTERRUPT(Ultrasonic_Tim3Ch6Isr, 0, );

/* private 함수 선언 */
//static void delayUs(uint32 us);

static void setPinOutput(UltrasonicSensor* sensor);
static void setPinInput(UltrasonicSensor* sensor);
static void writePinHigh(UltrasonicSensor* sensor);
static void writePinLow(UltrasonicSensor* sensor);

static void initGtmTim(void);
//static void initTbu0(void); ?

static uint16 echoUsToDistanceMm(uint32 echoUs);

static uint16 measureDistanceMm(UltrasonicSensor* sensor);


/* static 함수 구현 */
static void initGtmTim(void) {
    IfxGtm_enable(&MODULE_GTM);

    
}

static uint16 echoUsToDistanceMm(uint32 echoUs) {
    uint32 distanceMm = ((echoUs * SONIC_SPEED) + 1000u) / 2000u;
    
    if((distanceMm < ULTRASONIC_MIN_DISTANCE_MM) || (distanceMm > ULTRASONIC_MAX_DISTANCE_MM)) {
        return ULTRASONIC_INVALID_DISTANCE_MM;
    }

    return (uint16)distanceMm;
}

static uint16 measureDistanceMm(UltrasonicSensor* sensor) {
    if(g_isInitializd == FALSE) {
        return ULTRASONIC_INVALID_DISTANCE_MM;
    }

    if
}


/* Public 함수 */
void UltrasonicApp_Init(void) {
    if(g_isInitializd == TRUE) return;

    for(int i = 0; i < ULTRASONIC_SENSOR_COUNT; i++) {
        g_sensors[i].durationUs = 0u;
        g_sensors[i].distanceMm = ULTRASONIC_INVALID_DISTANCE_MM;
    }

    g_measureState = ULTRASONIC_MEASURE_IDLE;
    g_activeSensorIdx = 0xFF;

    g_echoRiseUs = 0u;
    g_echoDurationUs = 0u;
    g_measuredDistanceMm = ULTRASONIC_INVALID_DISTANCE_MM;
    
    g_waitingTaskHandle = NULL;

    initGtmTim();

    g_isInitializd = TRUE;
}
