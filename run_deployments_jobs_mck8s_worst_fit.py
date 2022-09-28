# With improvements to implementation
import os
import pandas as pd
import time

job_template = '''cat <<EOF | kubectl create -f -
apiVersion: fogguru.eu/v1
kind: MultiClusterJob
metadata:
  name: {job_name}
spec:
  placementPolicy: worst-fit
  ttlSecondsAfterFinished: 10
  template:
    spec:
      containers:
      - name: {job_name}
        env:
          - name: STRESS_VM
            value: "4"
          - name: STRESS_VM_BYTES
            value: "{memory_req_byte}"
          - name: STRESS_TIMEOUT
            value: "{sleep_time}"
        image: chuangtw/stress-ng:latest
        resources:
            requests:
              memory: "{memory_req}Mi"
              cpu: "{cpu_req}m"
            limits:
              memory: "{memory_req}Mi"
              cpu: "{cpu_req}m"              
      restartPolicy: Never
EOF'''

deployment_template = '''cat <<EOF | kubectl create -f -
apiVersion: fogguru.eu/v1
kind: MultiClusterDeployment
metadata:
  name: {deployment_name}
  labels:
    app: nginx
spec:
  placementPolicy: worst-fit
  replicas: 1
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: k8s.gcr.io/hpa-example
        resources:
          requests:
            memory: "{memory_req}Mi"
            cpu: "{cpu_req}m"
          limits:
            memory: "{memory_req}Mi"
            cpu: "{cpu_req}m"          
        ports:
        - containerPort: 80
EOF'''

task_events_csv_colnames = ['iat','duration','cpu','memory']         
task_events_df = pd.read_csv(os.path.join('/root/k8s_google_injection', 'synthetic_trace_10000.csv'), sep=',', header=None, index_col=False, 
                         names=task_events_csv_colnames)

request_log_colnames = ['timestamp', 'pod_name','duration', 'cpu', 'memory']
request_log = pd.DataFrame(columns=request_log_colnames)

# Run for 2 hours

test_duration = 1 * 60 * 60
finish_time = time.time() + test_duration

print("Experiment started running at: " + str(time.time()))
for index, row in task_events_df.iterrows():
    if index <= 1209:
    #if time.time() < finish_time:
        if int(row['iat']/10) <= 2 * 60:
            pod_name = "task" + str(index)
            cpu_request = int(10000.0*row['cpu'])
            memory_request = int(10000.0*row['memory'])
            duration = row['duration']/1000000
            sleep_arg = 'sleep ' + str(duration)
            command = '/bin/bash -c \'' + sleep_arg + '\''

            print("Sleep for " + str(row['iat']/10.0) + " seconds ...")
            time.sleep(row['iat']/10.0)
            
            command_create = job_template.format(job_name=pod_name, sleep_time=duration, memory_req=memory_request, memory_req_byte=memory_request_byte, cpu_req=cpu_request)

            #else:
                #pod_name = "deployment" + str(index)
                #command_create = deployment_template.format(deployment_name=pod_name, memory_req=memory_request, cpu_req=cpu_request)
            timestamp = time.time()
            os.system(command_create)
            request_log = request_log.append([{'timestamp':timestamp, 'pod_name':pod_name, 'duration':duration, 
                                 'cpu':cpu_request, 'memory':memory_request}],ignore_index=True)
            file_name = 'multi_cluster_scheduling_logs.csv' 
            request_log.to_csv(file_name) 
    else:
        break
       
print("DONE!!! Finished running at: " + str(time.time()))
