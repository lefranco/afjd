OPT=-O3
#OPT=-DDEBUG

LIBS =
CFLAGS = ${OPT} -Wall -ansi -pedantic  -W  \
	-Wundef -Wshadow -Wpointer-arith -Wbad-function-cast -Wcast-qual -Wcast-align -Wwrite-strings \
	-Wsign-compare -Waggregate-return -Wstrict-prototypes -Wmissing-prototypes -Winline \
	 -Wlong-long -Wmissing-declarations -Wnested-externs
#	-Wredundant-decls -Wconversion
CC = gcc

HEADER =
HEADER2 =

OBJECTS =  traducteur.o 
OBJECTS2 =

SOURCES = traducteur.c 

%.o: %.c
	${CC} -c $< ${CFLAGS} ${LIBS}

traducteur: ${OBJECTS} ${OBJECTS2}
	${CC} -o traducteur ${OBJECTS} ${OBJECTS2} ${CFLAGS} ${LIBS}

${OBJECTS}: ${HEADER}

all:  traducteur

