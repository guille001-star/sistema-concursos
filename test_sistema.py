import requests

BASE_URL = "http://127.0.0.1:5000/api"

# Texto de prueba (fragmento del PDF real)
texto_listado = """
ADMINISTRACION DE LAS ORGANIZACIONES CICLO SUPERIOR (OEA) (EPJA) "Cat. DOCENTE"
11808 24748844 FORTUNA MARCELO ALEJAN Ramon de Miguel 211 TREVELIN 280-466343 D 27,01
15998 30224660 FLEITAS ROMINA VANESA El Michay 544 EPUYEN 294-483419 D 26,82
02471 33927292 GARNICA NOEMI ADELA Alberdi 760 EL MAITEN 2945-59456 D 24,99

ADMINISTRACION DE LAS ORGANIZACIONES CICLO SUPERIOR (OEA) (EPJA) "Cat. HABILITANTE"
17096 25658693 JAIME GABRIELA ANDREA Pasteur 1293 ESQUEL 2945-41643 H 20,55
10324 26326592 SANPEDRO YANINA LORENA Pasaje La Pampa 1004 EL MAITEN 294-640917 H 11,34

ADMINISTRACION DE LAS ORGANIZACIONES CICLO SUPERIOR (OEA) (EPJA) "Cat. SUPLETORIO"
17259 26868329 CARDOSO MARIA DEL VALL San Francisco d 1258 COMODORO RIVAD 280-427537 S 18,75
18010 28137653 RODRIGUEZ LUCIA CAROLI Ap Iwan 682 TREVELIN 2945-44003 S 18,70

CIRCUITOS TURISTICOS CICLO SUPERIOR (OT) "Fuera de Listado"
21* 10774 34663560 CAINECHU LORENA JUDIT Alsina 1957 ESQUEL 2945-54847 T 0,00
"""

print("Cargando listado oficial (texto)...")
response = requests.post(f"{BASE_URL}/cargar-listado", json={"texto": texto_listado})
print(f"OK {response.json()}\n")

print("Listando docentes cargados...")
response = requests.get(f"{BASE_URL}/docentes")
docentes = response.json()
print(f"Total docentes: {len(docentes)}")
for doc in docentes[:5]:
    print(f"  - {doc['nombre']} ({doc['categoria']} - {doc['puntaje']})")
print()

print("Creando concurso de prueba...")
# Usar un número único para evitar conflictos
import random
numero_concurso = f"TEST-{random.randint(1000, 9999)}/2026"
response = requests.post(f"{BASE_URL}/concurso", json={
    "numero": numero_concurso,
    "titulo": "Administracion EPJA - Escuela 788",
    "espacio_curricular": "ADMINISTRACION DE LAS ORGANIZACIONES CICLO SUPERIOR (OEA) (EPJA)",
    "caracter_cargo": "SUPLETORIO"
})

if response.status_code == 201:
    print(f"OK {response.json()}\n")
    concurso_id = response.json().get("id")
else:
    print(f"Error al crear concurso: {response.json()}")
    exit(1)

print("Registrando inscripciones...")
inscripciones = [
    {"concurso_id": concurso_id, "dni": "24748844"},  # FORTUNA (D - 27,01)
    {"concurso_id": concurso_id, "dni": "25658693"},  # JAIME (H - 20,55)
    {"concurso_id": concurso_id, "dni": "26868329"},  # CARDOSO (S - 18,75)
    {"concurso_id": concurso_id, "dni": "34663560"},  # CAINECHU (T - 0,00)
]

for insc in inscripciones:
    response = requests.post(f"{BASE_URL}/inscripcion", json=insc)
    print(f"  OK {response.json()}")

print()

print("Generando orden de merito...")
response = requests.post(f"{BASE_URL}/concurso/{concurso_id}/merito")

if response.status_code == 200:
    resultado = response.json()
    
    print("\nORDEN DE MERITO FINAL:")
    print("=" * 80)
    for item in resultado:
        ganador = " GANADOR" if item['es_ganador'] else ""
        print(f"Posicion {item['orden']}: {item['nombre']} {ganador}")
        print(f"  DNI: {item['dni']} | Categoria: {item['categoria']} | Puntaje: {item['puntaje']}")
        print(f"  Estado concurso: {item['estado_concurso']}")
        print("-" * 80)
else:
    print(f"Error: {response.status_code}")
    print(response.text)
