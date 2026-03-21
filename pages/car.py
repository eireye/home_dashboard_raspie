import streamlit as st
from streamlit_autorefresh import st_autorefresh
import os
from dotenv import load_dotenv

load_dotenv()

@st.cache_data(ttl=300)
def get_car_status():
    try:
        from weconnect import weconnect
        from weconnect.domain import Domain

        username = os.getenv('VW_USERNAME')
        password = os.getenv('VW_PASSWORD')

        if not username or not password:
            return {"error": "VW_USERNAME og VW_PASSWORD mangler i .env"}

        wc = weconnect.WeConnect(
            username=username,
            password=password,
            updateAfterLogin=False,
            loginOnInit=False,
            updateCapabilities=False,
            updatePictures=False,
        )
        wc.login()
        wc.update(selective=[Domain.CHARGING, Domain.ACCESS, Domain.MEASUREMENTS])

        vehicles = list(wc.vehicles.values())
        if not vehicles:
            return {"error": "Ingen kjøretøy funnet på denne kontoen"}

        vehicle = vehicles[0]
        result = {
            "name": vehicle.nickname.value if hasattr(vehicle, 'nickname') and vehicle.nickname.enabled else "ID.Buzz",
            "vin": vehicle.vin.value if hasattr(vehicle, 'vin') else "",
        }

        # Battery & range
        charging_domain = vehicle.domains.get('charging', {})
        battery = charging_domain.get('batteryStatus')
        if battery and battery.enabled:
            if battery.currentSOC_pct.enabled:
                result['soc_pct'] = battery.currentSOC_pct.value
            if battery.cruisingRangeElectric_km.enabled:
                result['range_km'] = battery.cruisingRangeElectric_km.value

        # Charging status
        charging = charging_domain.get('chargingStatus')
        if charging and charging.enabled:
            if charging.chargingState.enabled:
                result['charging_state'] = str(charging.chargingState.value.value)
            if charging.remainingChargingTimeToComplete_min.enabled:
                result['charging_remaining_min'] = charging.remainingChargingTimeToComplete_min.value
            if charging.chargePower_kW.enabled:
                result['charge_power_kw'] = charging.chargePower_kW.value

        # Plug status
        plug = charging_domain.get('plugStatus')
        if plug and plug.enabled:
            if plug.plugConnectionState.enabled:
                result['plug_state'] = str(plug.plugConnectionState.value.value)

        # Lock/access status
        access_domain = vehicle.domains.get('access', {})
        access = access_domain.get('accessStatus')
        if access and access.enabled:
            if access.overallStatus.enabled:
                result['lock_status'] = str(access.overallStatus.value.value)
            if access.doorLockStatus.enabled:
                result['door_lock'] = str(access.doorLockStatus.value.value)

        # Odometer
        measurements_domain = vehicle.domains.get('measurements', {})
        odometer = measurements_domain.get('odometerMeasurement')
        if odometer and odometer.enabled:
            if odometer.odometer_km.enabled:
                result['odometer_km'] = odometer.odometer_km.value

        wc.disconnect()
        return result

    except Exception as e:
        return {"error": str(e)}


def charging_state_norwegian(state):
    mapping = {
        'charging': 'Lader',
        'ready for charging': 'Klar for lading',
        'not ready for charging': 'Ikke klar for lading',
        'conservation charging': 'Bevaringslading',
        'charge purpose reached and conservation mode': 'Mål nådd',
        'off': 'Av',
        'error': 'Feil',
        'unsupported': 'Ikke støttet',
    }
    return mapping.get(state.lower(), state)


def plug_state_norwegian(state):
    mapping = {
        'connected': 'Tilkoblet',
        'disconnected': 'Ikke tilkoblet',
    }
    return mapping.get(state.lower(), state)


def lock_status_norwegian(status):
    mapping = {
        'locked': 'Låst',
        'unlocked': 'Ulåst',
        'invalid': 'Ukjent',
        'unsupported': 'Ikke støttet',
    }
    return mapping.get(status.lower(), status)


def show():
    st_autorefresh(interval=300000, key="car_refresh")
    st.markdown("## 🚗 ID.Buzz")

    data = get_car_status()

    if 'error' in data:
        st.error(f"Kunne ikke hente bilstatus: {data['error']}")
        if "VW_USERNAME" in data['error']:
            st.info("Legg til VW_USERNAME og VW_PASSWORD i .env-filen.")
        return

    car_name = data.get('name', 'ID.Buzz')
    st.caption(car_name)

    col1, col2, col3 = st.columns(3)

    # Battery & range
    with col1:
        soc = data.get('soc_pct')
        if soc is not None:
            bar_color = "🟢" if soc >= 50 else ("🟡" if soc >= 20 else "🔴")
            st.markdown(f"**{bar_color} Batteri**")
            st.markdown(f"### {soc}%")
            st.progress(soc / 100)
        else:
            st.markdown("**🔋 Batteri**")
            st.caption("Ikke tilgjengelig")

        range_km = data.get('range_km')
        if range_km is not None:
            st.caption(f"🛣️ Rekkevidde: **{range_km} km**")

        odometer = data.get('odometer_km')
        if odometer is not None:
            st.caption(f"Kilometerstand: {odometer:,} km")

    # Charging status
    with col2:
        st.markdown("**⚡ Lading**")
        plug = data.get('plug_state')
        charging_state = data.get('charging_state')

        if plug:
            st.caption(f"Plugg: {plug_state_norwegian(plug)}")
        if charging_state:
            st.caption(f"Status: {charging_state_norwegian(charging_state)}")

        remaining = data.get('charging_remaining_min')
        if remaining and charging_state and 'charging' in charging_state.lower():
            hours, mins = divmod(remaining, 60)
            if hours:
                st.caption(f"Ferdig om: {hours}t {mins}m")
            else:
                st.caption(f"Ferdig om: {mins} min")

        power = data.get('charge_power_kw')
        if power and power > 0:
            st.caption(f"Effekt: {power} kW")

    # Lock status
    with col3:
        st.markdown("**🔒 Lås**")
        lock = data.get('lock_status')
        if lock:
            icon = "🔒" if 'lock' in lock.lower() else "🔓"
            st.markdown(f"### {icon}")
            st.caption(lock_status_norwegian(lock))
        else:
            st.caption("Ikke tilgjengelig")

    if data.get('vin'):
        st.caption(f"VIN: {data['vin']}")
