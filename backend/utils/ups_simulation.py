import time,threading

def generate_seq(filename="/opt/homebrew/etc/nut/simulation.seq"):
    with open(filename, "w") as f:
        base_state = {
            "battery.charge": 100,
            "battery.charge.low": 20,
            "battery.runtime": 5400,
            "device.mfr": "MGE UPS SYSTEMS",
            "device.model": "Pulsar Evolution 3000",
            "device.serial": "AF3Ennnnn",
            "device.type": "ups",
            "driver.debug": 0,
            "driver.flag.allow_killpower": 0,
            "driver.name": "dummy-ups",
            "driver.parameter.mode": "dummy-once",
            "driver.parameter.pollinterval": 2,
            "driver.parameter.port": "MGE_UPS_SYSTEMS__Pulsar_Evolution_3000__mge-shut__2.6.2__01.dev",
            "driver.parameter.synchronous": "auto",
            "driver.state": "updateinfo",
            "driver.version": "2.8.3",
            "driver.version.internal": "0.20",
            "input.frequency": 50,
            "input.voltage": 240,
            "outlet.1.autoswitch.charge.low": 0,
            "outlet.1.delay.shutdown": -1,
            "outlet.1.delay.start": -1,
            "outlet.1.desc": "PowerShare Outlet 1",
            "outlet.1.id": 1,
            "outlet.1.switch": 1,
            "outlet.1.switchable": 1,
            "outlet.2.autoswitch.charge.low": 0,
            "outlet.2.delay.shutdown": -1,
            "outlet.2.delay.start": -1,
            "outlet.2.desc": "PowerShare Outlet 2",
            "outlet.2.id": 2,
            "outlet.2.switch": 1,
            "outlet.2.switchable": 1,
            "outlet.desc": "Main Outlet",
            "outlet.id": 0,
            "outlet.switchable": 0,
            "output.frequency": 50,
            "output.voltage": 237,
            "output.voltage.nominal": 72,
            "ups.load": 10,
            "ups.mfr": "MGE UPS SYSTEMS",
            "ups.model": "Pulsar Evolution 3000",
            "ups.power.nominal": 3000,
            "ups.serial": "AF3Ennnnn",
            "ups.status": "OL CHRG",
            "ups.test.result": "Done and passed",
            "ups.timer.shutdown": -1,
            "ups.timer.start": -1
        }

        # 每筆狀態變化
        seq_changes = [
            {},  # 初始值
            {
                "input.voltage": 0,
                "ups.status": "OB DISCHRG",
                "battery.charge": 80,
                "battery.runtime": 4320,
                "ups.load": 20
            },
            {
                "battery.charge": 60,
                "battery.runtime": 3240,
                "ups.load": 30
            },
            {
                "battery.charge": 40,
                "battery.runtime": 2160,
                "ups.load": 40
            },
            {
                "battery.charge": 20,
                "battery.runtime": 1080,
                "ups.load": 50
            },
            {
                "battery.charge": 10,
                "battery.runtime": 300,
                "ups.load": 60
            },
            {
                "input.voltage": 240,
                "ups.status": "OL CHRG",
                "output.voltage": 237,
                "battery.charge": 20,
                "battery.runtime": 1080,
                "ups.load": 20
            },
            {
                "battery.charge": 40,
                "battery.runtime": 2160,
                "ups.load": 15
            },
            {
                "battery.charge": 60,
                "battery.runtime": 3240,
                "ups.load": 10
            },
            {
                "battery.charge": 80,
                "battery.runtime": 4320
            },
            {
                "battery.charge": 100,
                "battery.runtime": 5400
            }
        ]

        index = 0
        while True:
            base_state.update(seq_changes[index])
            with open(filename, "w", encoding="utf-8") as f:
                for k, v in base_state.items():
                    f.write(f"{k}: {v}\n")
                f.write("\n")

            index = (index + 1) % len(seq_changes)
            time.sleep(60)


def start_background_ups_simulator():
    thread = threading.Thread(target=generate_seq, daemon=True)
    thread.start()