OPT=-O3
LIBS =
CFLAGS = ${OPT} -Wall -ansi -pedantic  -W  \
	-Wundef -Wshadow -Wpointer-arith -Wbad-function-cast -Wcast-qual -Wcast-align -Wwrite-strings \
	-Wsign-compare -Waggregate-return -Wstrict-prototypes -Wmissing-prototypes -Winline \
	-Wlong-long -Wmissing-declarations -Wnested-externs
#	-Wredundant-decls -Wconversion
CC = gcc

HEADER = define2.h  include2.h  protos2.h
HEADER2 = ../solveur/datas.h ../solveur/define.h ../solveur/includes.h ../solveur/protos.h ../solveur/struct.h

OBJECTS =  aideur.o
OBJECTS2 = ../solveur/decrit.o ../solveur/erreurs.o ../solveur/gestion.o ../solveur/convois.o ../solveur/parse.o ../solveur/langue.o ../solveur/utils.o parse2.o

SOURCES = aideur.c parse2.c

%.o : %.c
	${CC} -c $< -o $@ ${CFLAGS} ${LIBS}

aideur: ${OBJECTS} ${OBJECTS2}
	${CC} -o aideur ${OBJECTS} ${OBJECTS2} ${CFLAGS} ${LIBS}

${OBJECTS}: ${HEADER} ${HEADER2}

all:  aideur

