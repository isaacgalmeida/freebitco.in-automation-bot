from seleniumbase import SB

def verify_success(sb):
    sb.assert_element('img[alt="Logo Assembly"]', timeout=4)
    sb.sleep(3)

with SB(uc=True) as sb:
    sb.uc_open_with_reconnect("https://pace.coe.int/en/aplist/committees/9/commission-des-questions-politiques-et-de-la-democratie", 3)
    try:
        verify_success(sb)
    except Exception:
        if sb.is_element_visible('input[value*="Verify"]'):
            sb.uc_click('input[value*="Verify"]')
        else:
            sb.uc_gui_click_captcha()
        try:
            verify_success(sb)
        except Exception:
            raise Exception("Detected!")