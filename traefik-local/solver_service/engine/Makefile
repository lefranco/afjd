OPT=-O0

LIBS =
CFLAGS = ${OPT} -Wall -ansi -pedantic  -W \
	-Wundef -Wshadow -Wpointer-arith -Wbad-function-cast -Wcast-qual -Wcast-align -Wwrite-strings \
	-Wsign-compare -Waggregate-return -Wstrict-prototypes -Wmissing-prototypes -Winline \
	-Wlong-long -Wmissing-declarations -Wnested-externs
#	-Wredundant-decls -Wconversion
CC = gcc

HEADER = datas.h define.h includes.h protos.h struct.h

OBJECTS = decrit.o resoud.o solveur.o heuris.o erreurs.o convois.o gestion.o parse.o langue.o utils.o

SOURCES = decrit.c resoud.c solveur.c heuris.c erreurs.c convois.c gestion.c parse.c langue.c utils.c

%.o: %.c
	${CC} -c $< ${CFLAGS} ${LIBS}

solveur: ${OBJECTS}
	${CC} -o solveur ${OBJECTS} ${CFLAGS} ${LIBS} 

${OBJECTS}: ${HEADER}

all:  solveur
