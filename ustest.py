#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PCAN-USB / PCAN-USB FD CAN FD visualizer for UltrasonicDistanceCmd_t
IDE 실행 버튼으로 바로 실행 가능한 버전.

CAN message
- CAN ID: 0x200
- CAN FD DLC 12 => 24-byte frame
- Payload uses first 23 bytes

Payload layout, little-endian:
B0~B19  : 10 x uint16 distance [mm]
B20~B21 : int16 imuYaw [-180..180]
B22     : uint8 vehicleSpeed [0.1 km/h]
B23     : padding / unused

Special value:
- distance raw bytes FF FF, value 0xFFFF => Sensor Error
- distance values 0x0000..0xFFFE are valid distance values
"""

from __future__ import annotations

import math
import queue
import struct
import threading
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

import tkinter as tk
from tkinter import ttk, messagebox

try:
    import can  # type: ignore
except ImportError:
    can = None  # GUI는 켜고, 연결 버튼을 누를 때 에러를 보여준다.


# ================================================================
# IDE 실행용 기본 설정
# PyCharm / VS Code / Thonny 등에서 Run 버튼만 눌러도 이 값으로 실행된다.
# 필요하면 여기만 바꾸면 된다.
# ================================================================
PCAN_CHANNEL_DEFAULT = "PCAN_USBBUS1"
CAN_ID_DEFAULT = 0x200
AUTO_CONNECT_ON_START = True

# PCAN CAN FD bit timing preset
# 기본값: nominal 500 kbit/s, data 2 Mbit/s, f_clock 80 MHz
PCAN_FD_TIMING = {
    "f_clock_mhz": 80,
    "nom_brp": 10,
    "nom_tseg1": 12,
    "nom_tseg2": 3,
    "nom_sjw": 3,
    "data_brp": 5,
    "data_tseg1": 6,
    "data_tseg2": 1,
    "data_sjw": 1,
}

MAX_DISPLAY_MM = 2000
WARN_MM = 700
DANGER_MM = 300
SENSOR_ERROR_VALUE = 0xFFFF  # raw bytes FF FF

PAYLOAD_FORMAT = "<10HhB"   # 10 uint16, 1 int16, 1 uint8 = 23 bytes
PAYLOAD_SIZE = struct.calcsize(PAYLOAD_FORMAT)

SENSOR_NAMES = [
    "Front",
    "Front-Right",
    "Right-Front",
    "Right-Behind",
    "Behind-Right",
    "Behind",
    "Behind-Left",
    "Left-Behind",
    "Left-Front",
    "Front-Left",
]

# 화면상의 센서 위치. x, y는 Canvas 중심 기준 방향 벡터.
SENSOR_DIRS = [
    (0.0, -1.0),     # Front
    (0.72, -0.72),   # Front-Right
    (1.0, -0.28),    # Right-Front
    (1.0, 0.28),     # Right-Behind
    (0.72, 0.72),    # Behind-Right
    (0.0, 1.0),      # Behind
    (-0.72, 0.72),   # Behind-Left
    (-1.0, 0.28),    # Left-Behind
    (-1.0, -0.28),   # Left-Front
    (-0.72, -0.72),  # Front-Left
]


@dataclass(frozen=True)
class UltrasonicDistanceCmd:
    distances_mm: Tuple[int, ...]
    imu_yaw_deg: int
    vehicle_speed_kmh: float
    timestamp: float
    raw: bytes

    @property
    def sensor_error_names(self) -> Tuple[str, ...]:
        return tuple(
            name for name, mm in zip(SENSOR_NAMES, self.distances_mm)
            if is_sensor_error(mm)
        )


def is_sensor_error(mm: int) -> bool:
    """ECU가 거리값으로 FF FF를 보낸 경우. 센서 이상으로 표시한다."""
    return mm == SENSOR_ERROR_VALUE


def is_no_data(mm: int) -> bool:
    """거리로 쓰기 어려운 값. 센서 이상과는 별도로 회색 계열로 표시한다."""
    return False


def raw_distance_hex(raw: bytes, sensor_index: int) -> str:
    base = sensor_index * 2
    if len(raw) < base + 2:
        return "-- --"
    return f"{raw[base]:02X} {raw[base + 1]:02X}"


def decode_ultrasonic_payload(data: bytes, timestamp: Optional[float] = None) -> UltrasonicDistanceCmd:
    """Decode first 23 bytes of CAN FD payload as UltrasonicDistanceCmd_t."""
    if len(data) < PAYLOAD_SIZE:
        raise ValueError(f"payload too short: {len(data)} bytes, need at least {PAYLOAD_SIZE}")

    values = struct.unpack(PAYLOAD_FORMAT, data[:PAYLOAD_SIZE])
    distances = tuple(int(v) for v in values[:10])
    yaw = int(values[10])
    speed = int(values[11]) * 0.1

    return UltrasonicDistanceCmd(
        distances_mm=distances,
        imu_yaw_deg=yaw,
        vehicle_speed_kmh=speed,
        timestamp=time.time() if timestamp is None else timestamp,
        raw=bytes(data),
    )


def make_pcan_fd_bus(channel: str) -> Any:
    """
    PCAN CAN FD 초기화.
    ECU 쪽 CAN FD 설정과 반드시 맞춰야 한다.
    """
    if can is None:
        raise RuntimeError(
            "python-can이 설치되어 있지 않습니다.\n"
            "IDE 터미널 또는 CMD에서 한 번만 실행: python -m pip install python-can\n"
            "Windows에서 PCAN 사용 시 PEAK PCAN-Basic/드라이버도 필요합니다."
        )

    return can.Bus(  # type: ignore[union-attr]
        interface="pcan",
        channel=channel,
        fd=True,
        **PCAN_FD_TIMING,
    )


class CanReaderThread(threading.Thread):
    def __init__(self, channel: str, can_id: int, out_queue: queue.Queue, status_queue: queue.Queue):
        super().__init__(daemon=True)
        self.channel = channel
        self.can_id = can_id
        self.out_queue = out_queue
        self.status_queue = status_queue
        self._stop_event = threading.Event()
        self._bus: Optional[Any] = None

    def stop(self) -> None:
        self._stop_event.set()
        if self._bus is not None:
            try:
                self._bus.shutdown()
            except Exception:
                pass

    def run(self) -> None:
        try:
            self._bus = make_pcan_fd_bus(self.channel)
            self.status_queue.put(("connected", f"PCAN connected: {self.channel}, CAN ID 0x{self.can_id:X}"))
        except Exception as exc:
            self.status_queue.put(("error", f"PCAN 연결 실패: {exc}"))
            return

        while not self._stop_event.is_set():
            try:
                msg = self._bus.recv(timeout=0.1)
            except Exception as exc:
                self.status_queue.put(("error", f"CAN 수신 오류: {exc}"))
                time.sleep(0.5)
                continue

            if msg is None:
                continue

            if msg.arbitration_id != self.can_id:
                continue

            # 표준 ID 0x200만 받는 용도. 확장 ID를 쓰면 여기 조건 제거/수정.
            if msg.is_extended_id:
                continue

            try:
                decoded = decode_ultrasonic_payload(bytes(msg.data), timestamp=msg.timestamp)
            except ValueError as exc:
                self.status_queue.put(("warn", f"프레임 무시: {exc}"))
                continue

            self.out_queue.put(decoded)


class UltrasonicViewer(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Ultrasonic CAN FD Viewer - IDE Run")
        self.geometry("1080x760")
        self.minsize(960, 680)

        self.max_mm = MAX_DISPLAY_MM
        self.warn_mm = WARN_MM
        self.danger_mm = DANGER_MM

        self.data_queue: queue.Queue[UltrasonicDistanceCmd] = queue.Queue()
        self.status_queue: queue.Queue[Tuple[str, str]] = queue.Queue()
        self.reader: Optional[CanReaderThread] = None

        self.last_data: Optional[UltrasonicDistanceCmd] = None
        self.last_rx_wall_time = 0.0
        self.rx_count = 0

        self.channel_var = tk.StringVar(value=PCAN_CHANNEL_DEFAULT)
        self.can_id_var = tk.StringVar(value=f"0x{CAN_ID_DEFAULT:X}")

        self._build_ui()
        self.after(50, self._poll_queues)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        if AUTO_CONNECT_ON_START:
            self.after(200, self.connect_can)

    def _build_ui(self) -> None:
        main = ttk.Frame(self, padding=12)
        main.pack(fill=tk.BOTH, expand=True)

        controls = ttk.Frame(main)
        controls.pack(fill=tk.X)

        ttk.Label(controls, text="PCAN Channel").pack(side=tk.LEFT)
        ttk.Entry(controls, textvariable=self.channel_var, width=18).pack(side=tk.LEFT, padx=(6, 14))

        ttk.Label(controls, text="CAN ID").pack(side=tk.LEFT)
        ttk.Entry(controls, textvariable=self.can_id_var, width=10).pack(side=tk.LEFT, padx=(6, 14))

        self.connect_button = ttk.Button(controls, text="Connect / Reconnect", command=self.connect_can)
        self.connect_button.pack(side=tk.LEFT)
        ttk.Button(controls, text="Disconnect", command=self.disconnect_can).pack(side=tk.LEFT, padx=(6, 0))

        self.meta_var = tk.StringVar(value="RX: 0 | Yaw: -- deg | Speed: -- km/h | Age: -- ms | Sensor Error: 0")
        ttk.Label(controls, textvariable=self.meta_var, font=("Segoe UI", 10)).pack(side=tk.RIGHT)

        status_row = ttk.Frame(main)
        status_row.pack(fill=tk.X, pady=(8, 0))
        self.status_var = tk.StringVar(value="Ready. IDE 실행 후 자동 연결을 시도합니다.")
        ttk.Label(status_row, textvariable=self.status_var, font=("Segoe UI", 11, "bold")).pack(side=tk.LEFT)

        body = ttk.Frame(main)
        body.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        self.canvas = tk.Canvas(body, bg="#11151c", highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        side = ttk.Frame(body, width=310)
        side.pack(side=tk.RIGHT, fill=tk.Y, padx=(12, 0))
        side.pack_propagate(False)

        ttk.Label(side, text="Sensor Values", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 8))
        self.sensor_vars: Dict[str, tk.StringVar] = {}
        for name in SENSOR_NAMES:
            var = tk.StringVar(value=f"{name}: ----")
            self.sensor_vars[name] = var
            ttk.Label(side, textvariable=var, font=("Consolas", 10)).pack(anchor="w", pady=2)

        ttk.Separator(side).pack(fill=tk.X, pady=12)
        ttk.Label(side, text="Legend", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        ttk.Label(
            side,
            text=(
                f"Sensor Error : FF FF / 0xFFFF\n"
                f"Valid Range  : 0x0000 .. 0xFFFE\n"
                f"Danger       : < {self.danger_mm} mm\n"
                f"Warning      : < {self.warn_mm} mm\n"
                f"Normal       : >= {self.warn_mm} mm"
            ),
            font=("Consolas", 9),
        ).pack(anchor="w", pady=(4, 0))

        ttk.Separator(side).pack(fill=tk.X, pady=12)
        ttk.Label(side, text="Sensor Error List", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        self.error_list_var = tk.StringVar(value="None")
        ttk.Label(side, textvariable=self.error_list_var, font=("Consolas", 9), wraplength=290).pack(anchor="w", pady=(4, 0))

        ttk.Separator(side).pack(fill=tk.X, pady=12)
        ttk.Label(side, text="Payload", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        self.raw_var = tk.StringVar(value="--")
        ttk.Label(side, textvariable=self.raw_var, font=("Consolas", 9), wraplength=290).pack(anchor="w", pady=(4, 0))

        ttk.Separator(side).pack(fill=tk.X, pady=12)
        ttk.Label(side, text="Bit Timing", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        ttk.Label(
            side,
            text="Nominal 500 kbit/s\nData 2 Mbit/s\nClock 80 MHz",
            font=("Consolas", 9),
        ).pack(anchor="w", pady=(4, 0))

        self.canvas.bind("<Configure>", lambda _event: self._redraw())

    def connect_can(self) -> None:
        self.disconnect_can(show_status=False)

        try:
            can_id = int(self.can_id_var.get().strip(), 0)
        except ValueError:
            messagebox.showerror("CAN ID 오류", "CAN ID는 0x200 또는 512 같은 정수 형식으로 입력해줘.")
            return

        channel = self.channel_var.get().strip() or PCAN_CHANNEL_DEFAULT
        self.data_queue = queue.Queue()
        self.status_queue = queue.Queue()
        self.reader = CanReaderThread(channel, can_id, self.data_queue, self.status_queue)
        self.reader.start()
        self.status_var.set(f"🔌 Connecting {channel}, ID 0x{can_id:X} ...")

    def disconnect_can(self, show_status: bool = True) -> None:
        if self.reader is not None:
            self.reader.stop()
            self.reader = None
        if show_status:
            self.status_var.set("⏸ Disconnected")

    def _poll_queues(self) -> None:
        while True:
            try:
                kind, text = self.status_queue.get_nowait()
            except queue.Empty:
                break
            prefix = {"connected": "✅", "warn": "⚠", "error": "⛔"}.get(kind, "ℹ")
            self.status_var.set(f"{prefix} {text}")

        updated = False
        while True:
            try:
                self.last_data = self.data_queue.get_nowait()
            except queue.Empty:
                break
            self.rx_count += 1
            self.last_rx_wall_time = time.time()
            updated = True

        if updated:
            self._update_labels()
            self._redraw()
        else:
            self._update_meta_only()

        self.after(50, self._poll_queues)

    def _update_labels(self) -> None:
        if self.last_data is None:
            return

        data = self.last_data
        for idx, (name, value) in enumerate(zip(SENSOR_NAMES, data.distances_mm)):
            raw_hex = raw_distance_hex(data.raw, idx)
            if is_sensor_error(value):
                text = f"{name:<13}: SENSOR ERROR  ({raw_hex})"
            else:
                cm = value / 10.0
                text = f"{name:<13}: {value:5d} mm  ({cm:6.1f} cm)"
            self.sensor_vars[name].set(text)

        errors = data.sensor_error_names
        self.error_list_var.set("None" if not errors else ", ".join(errors))
        self.raw_var.set(" ".join(f"{b:02X}" for b in data.raw[:24]))
        self._update_meta_only()

    def _update_meta_only(self) -> None:
        if self.last_data is None:
            return
        age_ms = int((time.time() - self.last_rx_wall_time) * 1000) if self.last_rx_wall_time else 0
        data = self.last_data
        error_count = len(data.sensor_error_names)
        self.meta_var.set(
            f"RX: {self.rx_count} | Yaw: {data.imu_yaw_deg:+d} deg | "
            f"Speed: {data.vehicle_speed_kmh:.1f} km/h | Age: {age_ms} ms | "
            f"Sensor Error: {error_count}"
        )

    def _color_for_distance(self, mm: int) -> str:
        if is_sensor_error(mm):
            return "#ff4fd8"   # sensor error: 눈에 확 띄는 분홍/보라
        if mm < self.danger_mm:
            return "#ff3b30"   # danger
        if mm < self.warn_mm:
            return "#ffb020"   # warning
        return "#34c759"       # normal

    def _distance_radius(self, mm: int, min_r: float, max_r: float) -> float:
        if is_sensor_error(mm):
            return max_r
        clipped = max(0, min(mm, self.max_mm))
        return min_r + (clipped / self.max_mm) * (max_r - min_r)

    def _redraw(self) -> None:
        c = self.canvas
        c.delete("all")
        w = max(c.winfo_width(), 1)
        h = max(c.winfo_height(), 1)
        cx, cy = w / 2, h / 2
        scale = min(w, h)

        # 배경 거리 링
        for ratio, label in ((0.20, "near"), (0.32, "mid"), (0.44, "far")):
            rr = scale * ratio
            c.create_oval(cx - rr, cy - rr, cx + rr, cy + rr, outline="#2b3340", width=1)
            c.create_text(cx + rr + 22, cy, text=label, fill="#566172", font=("Segoe UI", 8))

        # 차량 본체
        car_w, car_h = scale * 0.18, scale * 0.32
        c.create_rectangle(
            cx - car_w / 2,
            cy - car_h / 2,
            cx + car_w / 2,
            cy + car_h / 2,
            fill="#d9dee7",
            outline="#ffffff",
            width=2,
        )
        c.create_polygon(
            cx,
            cy - car_h / 2 - 18,
            cx - 18,
            cy - car_h / 2 + 10,
            cx + 18,
            cy - car_h / 2 + 10,
            fill="#7aa2ff",
            outline="#ffffff",
        )
        c.create_text(cx, cy, text="CAR", fill="#121722", font=("Segoe UI", 15, "bold"))

        if self.last_data is None:
            c.create_text(
                cx,
                cy + car_h / 2 + 50,
                text="Waiting for CAN FD frame ID 0x200...",
                fill="#d9dee7",
                font=("Segoe UI", 14, "bold"),
            )
            return

        min_r = scale * 0.18
        max_r = scale * 0.43

        for idx, (name, vec) in enumerate(zip(SENSOR_NAMES, SENSOR_DIRS)):
            mm = self.last_data.distances_mm[idx]
            color = self._color_for_distance(mm)
            r = self._distance_radius(mm, min_r, max_r)
            x = cx + vec[0] * r
            y = cy + vec[1] * r

            # 센서 방향 레이
            dash = () if is_sensor_error(mm) else (6, 5)
            c.create_line(cx, cy, x, y, fill=color, width=4, dash=dash)

            dot = 14
            c.create_oval(x - dot, y - dot, x + dot, y + dot, fill=color, outline="#f4f7fb", width=2)

            if is_sensor_error(mm):
                # FF FF 센서 이상은 X 표시로 일반 위험거리와 완전히 구분
                c.create_line(x - 10, y - 10, x + 10, y + 10, fill="#11151c", width=4)
                c.create_line(x + 10, y - 10, x - 10, y + 10, fill="#11151c", width=4)
                value_text = "SENSOR\nERROR\nFF FF"
            else:
                value_text = f"{mm} mm"

            label_r = r + 38
            lx = cx + vec[0] * label_r
            ly = cy + vec[1] * label_r
            c.create_text(
                lx,
                ly,
                text=f"{name}\n{value_text}",
                fill="#f4f7fb",
                font=("Segoe UI", 9, "bold"),
                justify=tk.CENTER,
            )

        # yaw 바늘
        yaw = math.radians(self.last_data.imu_yaw_deg - 90)
        needle_len = scale * 0.13
        nx = cx + math.cos(yaw) * needle_len
        ny = cy + math.sin(yaw) * needle_len
        c.create_line(cx, cy, nx, ny, fill="#00d1ff", width=3, arrow=tk.LAST)
        c.create_text(
            cx,
            cy + car_h / 2 + 28,
            text=f"Yaw {self.last_data.imu_yaw_deg:+d}°   Speed {self.last_data.vehicle_speed_kmh:.1f} km/h",
            fill="#f4f7fb",
            font=("Segoe UI", 12, "bold"),
        )

    def _on_close(self) -> None:
        self.disconnect_can(show_status=False)
        self.destroy()


def main() -> None:
    app = UltrasonicViewer()
    app.mainloop()


if __name__ == "__main__":
    main()
