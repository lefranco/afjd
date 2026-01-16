#!/usr/bin/env bash

# sshpass needs to be installed on backup machine
# sqlite3 needs to be installed on server
# mongodb needs to be installed on backup machine
# rclone needs to be installed on backup machine (and credentials in ~/.config/rclone/rclone.conf)

SERVER_USERNAME="ubuntu"
SERVER_ADDRESS="37.59.100.228"
MONGODB_PORT=27017
MONGODB_DATABASE_NAME=nodebb
MONGODB_DATABASE_USER=nodebb
GOOGLE_DRIVE=backup_diplomania

# If script recives interruption signal, it stops completely
trap "exit" INT

# Time of script execution
start_time=$(date +%s)

# Backup  time stamp
now=$(date +%Y%m%d)

# Only one possible parameter
if [ ! "$1" == "-f" ]; then
    echo "Use -f parameter for fast mode (only Flasks APIs)"
    echo
fi

# Need server machine password
if [ -z "${SERVER_PASSWORD}" ]; then
    echo "Please define SERVER_PASSWORD !"
    exit 1
fi

# Create a fresh backup dir
if [ -d ./backups ]; then
    rm -fr ./backups
fi
mkdir ./backups

echo "================"
echo "Backuping Flask APIs ..."
echo "================"
echo

for service in users players games; do

    # do backup 
    echo "Backuping ${service}..."
    backup_distant_file=/tmp/backup_db_${service}_${now}.db
    cmd="sqlite3 ./api_flask/${service}_service/db/${service}.db '.backup ${backup_distant_file}'"
    sshpass -p "${SERVER_PASSWORD}" ssh ${SERVER_USERNAME}@${SERVER_ADDRESS} ${cmd}

    # do dump
    echo "Dumping ${service}..."
    dump_distant_file=/tmp/dump_db_${service}_${now}.sql.gz
    cmd="sqlite3 ./api_flask/${service}_service/db/${service}.db .dump | gzip > ${dump_distant_file}"
    sshpass -p "${SERVER_PASSWORD}" ssh ${SERVER_USERNAME}@${SERVER_ADDRESS} ${cmd}

    # bring backup and dump here on backup machine
    echo "Bringing locally ${service} file"
    backup_local_file=backup_db_${service}_${now}.db
    sshpass -p "${SERVER_PASSWORD}" scp ${SERVER_USERNAME}@${SERVER_ADDRESS}:${backup_distant_file} ${backup_local_file}
    dump_local_file=dump_db_${service}_${now}.sql.gz
    sshpass -p "${SERVER_PASSWORD}" scp ${SERVER_USERNAME}@${SERVER_ADDRESS}:${dump_distant_file} ${dump_local_file}

    # delete backup and dump from server
    echo "Deleting from server ${service} file"
    cmd="rm ${backup_distant_file} && rm ${dump_distant_file}"
    sshpass -p "${SERVER_PASSWORD}" ssh ${SERVER_USERNAME}@${SERVER_ADDRESS} ${cmd}

    # move to backup dir
    echo "Moving to backup dir ${service} file"
    mv ${backup_local_file} ./backups/
    mv ${dump_local_file} ./backups/

    echo

done

if [ "$1" == "-f" ]; then
    echo "Fast mode selected. Exiting"
    exit 0
fi

echo "================"
echo "Backuping Forum ..."
echo "================"
echo

if [ -z "${MONGODB_DATABASE_PASSWORD}" ]; then
    echo "Please define MONGODB_PASSWORD !"
    exit 1
fi

backup_local_dir=nodebb-${now}
backup_local_file=nodebb-${now}.tar

echo "Backuping forum database"
if [ -d ${backup_local_dir} ]; then
    rm -fr ${backup_local_dir}
fi
mkdir ${backup_local_dir}
mongodump --host ${SERVER_ADDRESS} --port ${MONGODB_PORT} --db ${MONGODB_DATABASE_NAME} --out ${backup_local_dir} --gzip --authenticationMechanism SCRAM-SHA-256 --username ${MONGODB_DATABASE_USER} --password ${MONGODB_DATABASE_PASSWORD} 2>&1 >/dev/null

# tar dir to single file
tar cf ${backup_local_file} ${backup_local_dir}
rm -fr ${backup_local_dir}

# move to backup dir
echo "Moving to backup mongodb file"
mv ${backup_local_file} ./backups/

echo

echo "Bringing locally uploads files"
backup_local_directory=./uploads-${now}
if [ -d ${backup_local_directory} ]; then
    rm -fr ${backup_local_directory}
fi
backup_distant_directory=/home/ubuntu/forum_nodebb/data/nodebb/uploads
sshpass -p "${SERVER_PASSWORD}" scp -r ${SERVER_USERNAME}@${SERVER_ADDRESS}:${backup_distant_directory} ${backup_local_directory}

echo "Compressing uploads dir"
backup_local_file=uploads-${now}.tar.gz
tar -czf ${backup_local_file} ${backup_local_directory}
rm -fr ${backup_local_directory}

echo "Moving to backup dir uploads file"
mv ${backup_local_file} ./backups/

echo

echo "================"
echo "Backuping Wikis ..."
echo "================"
echo

for wiki in dokuwiki-data dokuwiki-data2; do

    echo "Backuping ${wiki}"
    echo

    backup_local_directory=./${wiki}-${now}
    if [ -d ${backup_local_directory} ]; then
        rm -fr ${backup_local_directory}
    fi

    for item in data/pages data/media data/meta conf ; do

        echo "Bringing locally ${wiki} ${item} files"
        backup_local_item_directory=./${backup_local_directory}/${item}
        mkdir -p ${backup_local_item_directory}
        backup_distant_item_directory=/home/ubuntu/wiki_doku/${wiki}/${item}
        sshpass -p "${SERVER_PASSWORD}" scp -r ${SERVER_USERNAME}@${SERVER_ADDRESS}:${backup_distant_item_directory} ${backup_local_item_directory}

    done

    echo "Compressing ${wiki}  dir"
    backup_local_file=${wiki}-${now}.tar.gz
    tar -czf ${backup_local_file} ${backup_local_directory}
    rm -fr ${backup_local_directory}

    echo "Moving to backup dir ${wiki} file"
    mv ${backup_local_file} ./backups/

done

echo

echo "================"
echo "Exporting to drive ..."
echo "================"
echo

rclone mkdir ${GOOGLE_DRIVE}:${now}

# Copying artefacts to drive
for artefact in $(ls ./backups) ; do
    echo "Moving ${artefact} to google drive..."
    rclone copy ./backups/${artefact} ${GOOGLE_DRIVE}:${now}/
done

# Removing artefacts from here
for artefact in $(ls ./backups) ; do
    echo "Deleting local ${artefact}..."
    rm ./backups/${artefact}
done

end_time=$(date +%s)
duration=$((end_time - start_time))

echo "Script took $duration seconds."

# TODO run endlessly
### now=$(date +%s)
### target=$(date -d "tomorrow 04:00" +%s)
### sleep $(( target - now ))

# TODO : send email
# mailutils msmtp msmtp-mta etc
# echo "content" | mail -s "subject" <dest>


