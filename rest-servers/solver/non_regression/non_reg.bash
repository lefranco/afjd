#!/usr/bin/bash


echo ==================================================================

if ! test "$1" = "" ; then
	ref=$1
	echo Comparaison avec resultats de $ref
	if ! test -r "$ref" ; then 	
		echo $ref : fichier introuvable
		exit 1
	fi
fi


typeset -i ok ko err amel regr

ok=0
ko=0
err=0

amel=0
regr=0

log=log_`date -u +%a_%b_%d_%H_%M_%S_%Z_%Y`.txt

diagref="???"

# si arret ctrl-C on efface le log
trap 'echo "Arret utilisateur"; rm -f $log; exit 0' 2

#Hasbro =====================

echo Reguliers Hasbro
for rep in `ls CAS_TEST/HASBRO` ; do 
	echo $rep
	for cas in `ls CAS_TEST/HASBRO/$rep/*.TXT` ; do 
		rep1="CAS_TEST/HASBRO/$rep"
		cas1=`basename $cas .TXT`
		./verifie_regulier.bash $cas1 $rep1 
		case $? in
			 0)   diag="Ok" ; ok=$ok+1 ;;
			 1)   diag="Echec" ; ko=$ko+1 ;;
			 255) diag="***ERREUR***" ; err=$err+1 ;;
		esac
		if test "$ref" != "" ; then
			diagref=`grep "$rep1/$cas1" $ref | cut -d : -f 2 | cut -d " " -f 2`
		fi
		if test "$diag" = "Ok" -a "$diagref" != "Ok" ; then 
			amel=$amel+1 
		fi
		if test  "$diag" != "Ok" -a "$diagref" = "Ok" ; then 
			regr=$regr+1 
		fi
		if test "$diag" != "$diagref" ; then 
			echo "	$cas1 :	$diag ($diagref)"
		else
			echo "	$cas1 :	$diag"
		fi
		echo "$rep1/$cas1 : $diag">>$log
	done
done

#Descartes =====================

echo
echo Reguliers Descartes :
for rep in `ls CAS_TEST/DESCARTES` ; do 
	echo $rep
	for cas in `ls CAS_TEST/DESCARTES/$rep/*.TXT` ; do 
		rep1="CAS_TEST/DESCARTES/$rep"
		cas1=`basename $cas .TXT`
		./verifie_regulier.bash $cas1 $rep1 D
		case $? in
			 0)   diag="Ok" ; ok=$ok+1 ;;
			 1)   diag="Echec" ; ko=$ko+1 ;;
			 255) diag="***ERREUR***" ; err=$err+1 ;;
		esac
		if test "$ref" != "" ; then
			diagref=`grep "$rep1/$cas1" $ref | cut -d : -f 2 | cut -d " " -f 2`
		fi
		if test "$diag" = "Ok" -a "$diagref" != "Ok" ; then 
			amel=$amel+1 
		fi
		if test  "$diag" != "Ok" -a "$diagref" = "Ok" ; then 
			regr=$regr+1 
		fi
		if test "$diag" != "$diagref" ; then 
			echo "	$cas1 :	$diag ($diagref)"
		else
			echo "	$cas1 :	$diag"
		fi
		echo "$rep1/$cas1 : $diag">>$log
	done
done

echo
echo Speciaux Descartes :
for rep in `ls CAS_TEST/DESCARTES_goofy` ; do 
	echo $rep
	for cas in `ls CAS_TEST/DESCARTES_goofy/$rep/*.bash` ; do 
		rep1="CAS_TEST/DESCARTES_goofy/$rep"
		cas1=`basename $cas .bash`
		pushd $rep1 >/dev/null
		./$cas1.bash #appel du test
		case $? in
			 0)   diag="Ok" ; ok=$ok+1 ;;
			 1)   diag="Echec" ; ko=$ko+1 ;;
			 255) diag="***ERREUR***" ; err=$err+1 ;;
		esac
		popd >/dev/null
		if test "$ref" != "" ; then
			diagref=`grep "$rep1/$cas1" $ref | cut -d : -f 2 | cut -d " " -f 2`
		fi
		if test "$diag" = "Ok" -a "$diagref" != "Ok" ; then 
			amel=$amel+1 
		fi
		if test  "$diag" != "Ok" -a "$diagref" = "Ok" ; then 
			regr=$regr+1 
		fi
		if test "$diag" != "$diagref" ; then 
			echo "	$cas1 :	$diag ($diagref)"
		else
			echo "	$cas1 :	$diag"
		fi
		echo "$rep1/$cas1 : $diag">>$log
	done
done

#DATC =====================

echo
echo Reguliers DATC :
for rep in `ls CAS_TEST/DATC` ; do 
	echo $rep
	for cas in `ls CAS_TEST/DATC/$rep/*.TXT` ; do 
		rep1="CAS_TEST/DATC/$rep"
		cas1=`basename $cas .TXT`
		./verifie_regulier.bash $cas1 $rep1 
		case $? in
			 0)   diag="Ok" ; ok=$ok+1 ;;
			 1)   diag="Echec" ; ko=$ko+1 ;;
			 255) diag="***ERREUR***" ; err=$err+1 ;;
		esac
		if test "$ref" != "" ; then
			diagref=`grep "$rep1/$cas1" $ref | cut -d : -f 2 | cut -d " " -f 2`
		fi
		if test "$diag" = "Ok" -a "$diagref" != "Ok" ; then 
			amel=$amel+1 
		fi
		if test  "$diag" != "Ok" -a "$diagref" = "Ok" ; then 
			regr=$regr+1 
		fi
		if test "$diag" != "$diagref" ; then 
			echo "	$cas1 :	$diag ($diagref)"
		else
			echo "	$cas1 :	$diag"
		fi
		echo "$rep1/$cas1 : $diag">>$log
	done
done

echo
echo Speciaux DATC :
for rep in `ls CAS_TEST/DATC_goofy` ; do 
	echo $rep
	for cas in `ls CAS_TEST/DATC_goofy/$rep/*.bash` ; do 
		rep1="CAS_TEST/DATC_goofy/$rep"
		cas1=`basename $cas .bash`
		pushd $rep1 >/dev/null
		./$cas1.bash #appel du test
		case $? in
			 0)   diag="Ok" ; ok=$ok+1 ;;
			 1)   diag="Echec" ; ko=$ko+1 ;;
			 255) diag="***ERREUR***" ; err=$err+1 ;;
		esac
		popd >/dev/null
		if test "$ref" != "" ; then
			diagref=`grep "$rep1/$cas1" $ref | cut -d : -f 2 | cut -d " " -f 2`
		fi
		if test "$diag" = "Ok" -a "$diagref" != "Ok" ; then 
			amel=$amel+1 
		fi
		if test  "$diag" != "Ok" -a "$diagref" = "Ok" ; then 
			regr=$regr+1 
		fi
		if test "$diag" != "$diagref" ; then 
			echo "	$cas1 :	$diag ($diagref)"
		else
			echo "	$cas1 :	$diag"
		fi
		echo "$rep1/$cas1 : $diag">>$log
	done
done


#DPTG =====================

echo
echo Reguliers DPTG :
for rep in `ls CAS_TEST/DPTG` ; do 
	echo $rep
	for cas in `ls CAS_TEST/DPTG/$rep/*.TXT` ; do 
		rep1="CAS_TEST/DPTG/$rep"
		cas1=`basename $cas .TXT`
		./verifie_regulier.bash $cas1 $rep1 
		case $? in
			 0)   diag="Ok" ; ok=$ok+1 ;;
			 1)   diag="Echec" ; ko=$ko+1 ;;
			 255) diag="***ERREUR***" ; err=$err+1 ;;
		esac
		if test "$ref" != "" ; then
			diagref=`grep "$rep1/$cas1" $ref | cut -d : -f 2 | cut -d " " -f 2`
		fi
		if test "$diag" = "Ok" -a "$diagref" != "Ok" ; then 
			amel=$amel+1 
		fi
		if test  "$diag" != "Ok" -a "$diagref" = "Ok" ; then 
			regr=$regr+1 
		fi
		if test "$diag" != "$diagref" ; then 
			echo "	$cas1 :	$diag ($diagref)"
		else
			echo "	$cas1 :	$diag"
		fi
		echo "$rep1/$cas1 : $diag">>$log
	done
done


#=====================================

echo
echo Synthese :
echo OK  : $ok 
echo Echec : $ko 
echo En erreur : $err 

echo
echo Ameliorations : $amel
echo Regressions : $regr

typeset -i pass
pass=$ok+$ko+$err
echo
echo Passes : $pass
