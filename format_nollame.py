import sys
import os
import re
import shutil
from datetime import datetime


def logger(message):
    with open("nollame_logs.log", "a") as f:
        f.write(f"{datetime.now()} - {message}\n")

def ContainsText(line):
    if bool(re.search(r'[a-zA-Z]',line)):
        return True
    return False

def Format_Detector(file):
    """
    Detecta los fallos del formato del archivo csv y los reporta a la salida estandar. 
    Ord: Headers, formato numerico, separadores, (ToF, N° columnas), solo caracteres necesarios, celulares con cel[0]=0 + tlf sin tlf[0]=0, tiene texto
    """
    headers = False
    numFormat = True
    separator = (False, None)
    columnsOk = (False, 0)
    hadCuotes = False
    phoneFormat = False
    containText = False

    def CuotesDetector(line):
        if re.search(r'"', line) or re.search(r"'", line):
                hadCuotes = True
        else:
            hadCuotes = False
        return hadCuotes

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
        
        if separator == (False, ""):
            separator = (False, None)

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
            
            hadCuotes = CuotesDetector(line)

            if i == 0:
                headers = HeadersDetector(line)
                separator = GetSeparator(line)
                if separator[1] != None:
                    columnsOk = GetColumns(lines, separator)
            else:
                containText = ContainsText(line)

            if i != 0:
                if line[0] == "0" and line[1] == "9":
                    numFormat = False

                if line[0] == "0" and line[1] != "9":
                    phoneFormat = True

    return headers, numFormat, separator, columnsOk, hadCuotes, phoneFormat, containText

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
    separatorChar = separator[1][0] if separator[1] != None else separator[1]
    columnsOk = corrections[3][0]
    hasCuotes = corrections[4]
    phoneStartsW0 = corrections[5]

    NewOutputFile(output_fileName)
    
    with open(file, 'r') as fcsv: # Guarda la entrada
        main_file_lines = fcsv.readlines()

    with open(output_fileName,'a') as fcsv: # Edita el archivo nuevo
        for i, line in enumerate(main_file_lines):

            if hasCuotes:
                line = re.sub(r'"', "", line)
                line = re.sub(r"'", "", line)
                line = re.sub(r"\t","", line)

            
            if i == 0 and not headers:
                fcsv.write('key,value\n')

            if not ContainsText(line):
                if not columnsOk:
                    if separator[1] != None:
                        line = main_file_lines[i].split(separatorChar)
                    else:
                        line = main_file_lines[i]

                    if separator[1] == None:
                        line = line.replace("\n","")
                        line = line + "," + line + "\n"
                    elif len(line) > 1:
                        line = line[0] + "," + line[1] + "\n"
                    elif separator[1] != None:
                        line = line[0] + "," + line[0] + "\n"
 
                
                if not numFormat and line[0] == "9": # Agrega un 0 al principio de los celulares que no lo tienen
                    line = line.replace(line,"0"+line)
                
                if (phoneStartsW0) and ("key" not in line) and (line[1] != "9"): # Saca el 0 de los telefonos fijos en caso de que todos los numeros tengan 0 al principio
                    line = line.replace(line,line[1:])

                if not separator[0] and separator[1] != None: # reemplaza el separador por comas 
                    line = line.replace(separatorChar,",")
                fcsv.write(line)

def Reporter(corrections):
    logger("---------------------------------------------------------------")
    logger("Contiene comillas dobles o simples: " + str(corrections[4]))
    logger("Tiene headers: " + str(corrections[0]))
    logger("Tiene formato numerico: "+ str(corrections[1]))
    logger("Tiene separador correcto: "+ str(corrections[2][0]))
    logger("Separador: " + str(corrections[2][1][0] if corrections[2][1] != None else "None"))
    logger("Cantidad de colunas: " + str(corrections[3][1]))
    logger("Los telefonos fijos empiezan con 0: " + str(corrections[5]))
    logger("Alguna linea tiene Texto: " + str(corrections[6]))
    logger("---------------------------------------------------------------\n\n\n")

def PendingCorrections(corrections):
    if False in corrections:
        return True
    else:
        return False

def usage():
    if len(sys.argv) >= 3 or len(sys.argv) < 2:
        logger("Usage: python format_nollame.py <input_file> [output_file]")
        sys.exit(1)


if __name__ == "__main__":

    usage()

    file = sys.argv[1]
    outputFolder = ".\\procesados"
    output_fileName = os.path.join(outputFolder, "nollame.csv")
    if (not os.path.isdir(outputFolder)):
        os.makedirs(outputFolder)
    full_route_file = os.path.abspath(file)
    


    corrections = Format_Detector(full_route_file)
    Reporter(corrections)

    if PendingCorrections(corrections):
        logger("El archivo no tiene el formato correcto")
        CSVformatter(corrections, full_route_file, output_fileName)
        logger("El archivo fue formateado en: " + str(output_fileName))
    else:
        logger("El archivo tiene el formato correcto")
        shutil.copy(file,output_fileName)
        logger("El archivo fue copiado en: " + str(output_fileName))

    sys.exit(1)
        