"""Prueba de https://www.casalicia.cl/appmiruta/ en Safari de iPhone (simulador de Xcode).

Solo lectura: abre la página sin sesión, desliza y toca el aviso de instalar.
No inicia sesión, no envía formularios y no cambia nada en el sitio.
Abre la página dos veces en total (una para los pasos 1 a 3 y otra para el 4).

Pasos:
 1. El aviso «Bienvenid@s a Casalicia · INSTALAR» se ve al abrir, sin deslizar.
 2. Sigue visible después de deslizar hacia abajo y hacia arriba.
 3. Al tocar INSTALAR aparece la instrucción «Toca ... y Agrega a Pantalla de Inicio».
 4. El formulario «Registrarse» y su botón se ven completos y nada los tapa.
 5. No aparece la cortina de carga (LoftLoader).
"""
import os
import sys
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.safari.options import Options

URL = "https://www.casalicia.cl/appmiruta/"
CAPTURAS = os.environ.get("CAPTURAS", "capturas")
os.makedirs(CAPTURAS, exist_ok=True)
resultados = []


def anotar(paso, ok, detalle=""):
    resultados.append((paso, ok, detalle))
    print(("BIEN  " if ok else "FALLA ") + paso + (" | " + detalle if detalle else ""), flush=True)


def captura(driver, nombre):
    driver.save_screenshot(os.path.join(CAPTURAS, nombre + ".png"))


ESTADO_AVISO = """
var b = document.getElementById('superpwa-sticky-bar');
if (!b) { return 'no existe'; }
var s = getComputedStyle(b), r = b.getBoundingClientRect();
var visible = s.display !== 'none' && s.visibility !== 'hidden' && r.height > 0 && r.bottom > 0 && r.top < innerHeight;
return visible ? 'visible' : 'oculto';
"""

# Devuelve los elementos del formulario de registro que algo tapa o que se salen de la pantalla.
TAPADOS_REGISTRO = """
var form = document.querySelector('form.woocommerce-form-register, form.register');
if (!form) { return ['no existe el formulario']; }
var piezas = Array.prototype.slice.call(form.querySelectorAll('label, input:not([type=hidden]), select, button[type=submit], button[name=register]'));
var problemas = [];
piezas.forEach(function (el) {
    if (el.offsetParent === null) { return; }
    el.scrollIntoView({block: 'center'});
    var r = el.getBoundingClientRect();
    var nombre = (el.name || el.id || el.tagName.toLowerCase() + ':' + (el.textContent || '').trim().slice(0, 20));
    if (r.left < 0 || r.right > innerWidth + 1) { problemas.push(nombre + ' se sale por el costado'); return; }
    var puntos = [[r.left + r.width / 2, r.top + r.height / 2], [r.left + 4, r.top + 4], [r.right - 4, r.bottom - 4]];
    puntos.forEach(function (p) {
        var arriba = document.elementFromPoint(p[0], p[1]);
        if (arriba && arriba !== el && !el.contains(arriba) && !arriba.contains(el)) {
            problemas.push(nombre + ' tapado por ' + (arriba.id || arriba.className || arriba.tagName));
        }
    });
});
return problemas;
"""


def abrir(driver):
    driver.get(URL)
    time.sleep(6)


def main():
    opciones = Options()
    opciones.set_capability("platformName", "iOS")
    opciones.set_capability("safari:useSimulator", True)
    opciones.set_capability("safari:deviceType", "iPhone")
    if os.environ.get("SIMULADOR_UDID"):
        opciones.set_capability("safari:deviceUDID", os.environ["SIMULADOR_UDID"])
    driver = webdriver.Safari(options=opciones)
    try:
        caps = driver.capabilities
        print("Navegador:", caps.get("browserName"), caps.get("browserVersion"), "| sistema:", caps.get("platformName"), flush=True)
        print("Agente:", driver.execute_script("return navigator.userAgent"), flush=True)

        abrir(driver)
        captura(driver, "1-al-abrir")
        cortina = driver.execute_script(
            "var l = document.getElementById('loftloader-wrapper');"
            "return l ? getComputedStyle(l).display + ' / ' + getComputedStyle(l).opacity : 'no existe';")
        anotar("5. Sin cortina de carga", cortina == "no existe", "cortina: " + cortina)
        estado = driver.execute_script(ESTADO_AVISO)
        anotar("1. Aviso visible al abrir, sin deslizar", estado == "visible", estado)

        driver.execute_script("window.scrollBy(0, 900);")
        time.sleep(1.5)
        abajo = driver.execute_script(ESTADO_AVISO)
        captura(driver, "2a-despues-de-bajar")
        driver.execute_script("window.scrollBy(0, -500);")
        time.sleep(1.5)
        arriba = driver.execute_script(ESTADO_AVISO)
        captura(driver, "2b-despues-de-subir")
        anotar("2. Aviso visible al bajar y al subir", abajo == "visible" and arriba == "visible",
               "al bajar: " + abajo + ", al subir: " + arriba)

        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)
        botones = driver.find_elements(By.XPATH, "//*[@id='superpwa-sticky-bar']//*[normalize-space(text())='INSTALAR']")
        if botones:
            botones[0].click()
        else:
            driver.find_element(By.ID, "superpwa-sticky-bar").click()
        time.sleep(2)
        captura(driver, "3-despues-de-tocar-instalar")
        instruccion = driver.execute_script(
            "var i = document.getElementById('superpwa-iossafari-a2h-banner');"
            "if (!i) { return ['no existe', '']; }"
            "var s = getComputedStyle(i), r = i.getBoundingClientRect();"
            "return [(s.display !== 'none' && r.height > 0) ? 'visible' : 'oculta', i.innerText.replace(/\\s+/g, ' ').trim()];")
        forma = "toque"
        if instruccion[0] != "visible":
            driver.execute_script("var b = document.getElementById('superpwa-sticky-bar'); if (b) { b.click(); }")
            time.sleep(2)
            captura(driver, "3b-despues-de-tocar-por-codigo")
            instruccion = driver.execute_script(
                "var i = document.getElementById('superpwa-iossafari-a2h-banner');"
                "if (!i) { return ['no existe', '']; }"
                "var s = getComputedStyle(i), r = i.getBoundingClientRect();"
                "return [(s.display !== 'none' && r.height > 0) ? 'visible' : 'oculta', i.innerText.replace(/\\s+/g, ' ').trim()];")
            forma = "toque por código"
        deteccion = driver.execute_script(
            "return 'safari:' + (/constructor/i.test(window.HTMLElement) || typeof window.safari !== 'undefined')"
            " + ' ios:' + /iPad|iPhone|iPod/.test(navigator.userAgent);")
        texto_ok = "Toca" in instruccion[1] and "Pantalla de Inicio" in instruccion[1]
        anotar("3. Instrucción para agregar a pantalla de inicio", instruccion[0] == "visible" and texto_ok,
               instruccion[0] + " (" + forma + ", " + deteccion + "): " + instruccion[1][:100])

        abrir(driver)
        problemas = driver.execute_script(TAPADOS_REGISTRO)
        boton = driver.find_elements(By.CSS_SELECTOR, "form.woocommerce-form-register button[name=register], form.register button[type=submit]")
        if boton:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", boton[0])
            time.sleep(1)
        captura(driver, "4-formulario-registrarse")
        anotar("4. Formulario Registrarse y su botón completos y sin tapar", not problemas and bool(boton),
               "; ".join(problemas[:6]) if problemas else ("botón encontrado" if boton else "no se encontró el botón"))
    finally:
        driver.quit()

    fallas = [r for r in resultados if not r[1]]
    print("\nResumen: %d de %d pasos bien." % (len(resultados) - len(fallas), len(resultados)), flush=True)
    resumen = os.environ.get("GITHUB_STEP_SUMMARY")
    if resumen:
        with open(resumen, "a", encoding="utf-8") as f:
            f.write("## App MiRuta en Safari de iPhone\n\n| Paso | Resultado | Detalle |\n|---|---|---|\n")
            for paso, ok, detalle in sorted(resultados):
                f.write("| %s | %s | %s |\n" % (paso, "Bien" if ok else "Falla", detalle.replace("|", "/")))
    sys.exit(1 if fallas else 0)


if __name__ == "__main__":
    main()
