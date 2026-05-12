import speech_recognition as sr

print("Buscando micrófonos disponibles...\n")
for index, name in enumerate(sr.Microphone.list_microphone_names()):
    print(f"Índice {index}: {name}")
