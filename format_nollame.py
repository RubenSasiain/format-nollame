import sys
import os
import re

def Format_Detector(file):
    """
    Detecta los fallos del formato del archivo csv y los reporta a la salida estandar. 
    Ord: Headers, formato numerico, separadores
    """
    headers = False
    numFormat = False
    separator = (False, "undef")
    columnsOk = (False, 0)
    onlyNeededCh = True
    phoneStartsW0 = False

    def CuotesDetector(line):
        if re.search(r'"', line) or re.search(r"'", line):
                onlyNeededCh = False
                # Se edita el archivo en memoria para poder analizarlo correctamente
                line = re.sub(r'"', "", line)
                line = re.sub(r"'", "", line)
        else:
            onlyNeededCh = True
        return onlyNeededCh

    def HeadersDetector(line):
        if 'key' in line and 'value' in line:
            headers = True
        else:
            headers = False
        return headers

    def GetSeparator(line):
        if ',' in line:
            separator = (True, ',')
        else: # Se combina RegEx con replaces para detectar el separador individualmente de los saltos de linea y otros caracteres
            separator = (False, re.sub(r"[A-Za-z0-9]", "", line.replace("\\n", "")).replace(" ", "").replace("\t", "").replace("\n", ""))

        return separator

    def GetColumns(lines, separator):
        if len(lines[i].split(separator[1])) == 2:
            columnsOk = (True, len(lines[i].split(separator[1])))
        else:
            columnsOk = (False, len(lines[i].split(separator[1])))
        return columnsOk

    with open(file, 'r') as fcsv:
        lines = fcsv.readlines()
        for i, line in enumerate(lines):
            
            onlyNeededCh = CuotesDetector(line)

            if i == 0:
                headers = HeadersDetector(line)

                separator = GetSeparator(line)

                columnsOk = GetColumns(lines, separator)

            if line[0] == "0" and line[1] != "9":
                phoneStartsW0 = True

            if i != 0:
                if line[0] == "0" and line[1] == "9":
                    numFormat = True

    return headers, numFormat, separator, columnsOk, onlyNeededCh, phoneStartsW0

def NewOutputFile(output_fileName):
    if os.path.exists(output_fileName): # Elimina el archivo si existe
            os.remove(output_fileName)

    with open(output_fileName, 'w') as fcsv: # Crea el archivo de salida en blanco
        pass

def CSVformatter(corrections, file, output_fileName):
    """
    Formatea el archivo csv con las correciones detectadas pasadas por corrections
    Y genera un archivo csv con la salida formateada
    """
    headers = corrections[0]
    numFormat = corrections[1]
    separator = corrections[2]
    separatorChar = separator[1][0]
    columnsOk = corrections[3][0]
    onlyNeededCh = corrections[4]
    phoneStartsW0 = corrections[5]
    
    NewOutputFile(output_fileName)
    
    with open(file, 'r') as fcsv: # Guarda la entrada
        main_file_lines = fcsv.readlines()

    with open(output_fileName,'a') as fcsv: # Edita el archivo nuevo
        for i, line in enumerate(main_file_lines):

            if not onlyNeededCh:
                line = re.sub(r'"', "", line)
                line = re.sub(r"'", "", line)
                line = re.sub(r"\t","", line)

            if i == 0 and not headers:
                fcsv.write('key,value\n')

            if not columnsOk:
                line = main_file_lines[i].split(separatorChar)
                if len(line) > 1:
                    line = line[0] + "," + line[1] + "\n"
                else:
                    line = line[0] + "," + line[0] + "\n"
            
            if not numFormat and line[0] == "9": # Agrega un 0 al principio de los celulares que no lo tienen
                line = line.replace(line,"0"+line)
            
            if (phoneStartsW0) and ("key" not in line) and (line[1] != "9"): # Saca el 0 de los telefonos fijos en caso de que todos los numeros tengan 0 al principio
                line = line.replace(line,line[1:])
                
            if not separator[0]: # reemplaza el separador por comas
                line = line.replace(separatorChar,",")
            fcsv.write(line)

def Reporter(corrections):
    print("\nContiene comillas dobles o simples: ", not corrections[4])
    print("Tiene headers: ",corrections[0])
    print("Tiene formato numerico: ",corrections[1])
    print("Tiene separador correcto: ",corrections[2][0])
    print("Separador: ",corrections[2][1][0])
    print("Cantidad de colunas:",corrections[3][1])
    print("Los telefonos fijos empiezan con 0: ",corrections[5], "\n")

def PendingCorrections(corrections):
    if not corrections[0] or not corrections[1] or not corrections[2][0] or not corrections[3][0] or not corrections[4]:
        return True
    else:
        return False

if __name__ == "__main__":
    if len(sys.argv) >= 4 or len(sys.argv) < 2:
        print("Usage: python format_nollame.py <input_file> [output_file]")
        sys.exit(1)
    
    file = sys.argv[1]

    full_route_file = os.path.abspath(file)

    output_fileName = sys.argv[2] if len(sys.argv) == 3 else full_route_file.replace(".csv", "_formatted.csv")

    corrections = Format_Detector(full_route_file)
    
    Reporter(corrections)

    if PendingCorrections(corrections):
        print("El archivo no tiene el formato correcto")
        CSVformatter(corrections, full_route_file, output_fileName)
        print("El archivo fue formateado en: ",output_fileName)
        sys.exit(1)
    else:
        print("El archivo tiene el formato correcto")