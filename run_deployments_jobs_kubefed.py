# Kubernetes federation

import os
import pandas as pd
import time

namespace_template = '''cat <<EOF | kubectl create -f -
apiVersion: v1
kind: Namespace
metadata:
  name: test-namespace
EOF'''

fnamespace_template = '''cat <<EOF | kubectl create -f -
apiVersion: types.kubefed.io/v1beta1
kind: FederatedNamespace
metadata:
  name: test-namespace
  namespace: test-namespace
spec:
  placement:
    clusters:
    - name: cluster1
    - name: cluster2
    - name: cluster3
    - name: cluster4
    - name: cluster5
EOF'''

os.system(namespace_template)
os.system(fnamespace_template)

print("Wait for 10 sec after creation of namespace")
time.sleep(10)

job_template = '''cat <<EOF | kubectl --context {location} create -f -
apiVersion: batch/v1
kind: Job
metadata:
  name: {job_name}
  namespace: test-namespace
spec:
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
            memory: {memory_req}Mi
            cpu: {cpu_req}m
          limits:
            cpu: {cpu_req}m
            memory: {memory_req}Mi
      restartPolicy: Never
EOF'''

deployment_template = '''cat <<EOF | kubectl create -f -
apiVersion: types.kubefed.io/v1beta1
kind: FederatedDeployment
metadata:
  name: {deployment_name}
  namespace: test-namespace
spec:
  template:
    metadata:
      labels:
        app: {deployment_name}
    spec:
      replicas: 1
      selector:
        matchLabels:
          app: {deployment_name}
      template:
        metadata:
          labels:
            app: {deployment_name}
        spec:
          containers:
          - image: eu.gcr.io/inlaid-index-271509/nginx
            name: {deployment_name}
            resources:
              requests:
                memory: {memory_req}Mi
                cpu: {cpu_req}m
              limits:
                memory: {memory_req}Mi
                cpu: {cpu_req}m
  placement:
    clusters:
    - name: {location}
---
apiVersion: types.kubefed.io/v1beta1
kind: FederatedService
metadata:
  name: {deployment_name}
  namespace: test-namespace
spec:
  template:
    spec:
      selector:
        app: {deployment_name}
      type: NodePort
      ports:
        - name: http
          port: 80
  placement:
    clusters:
    - name: {location}
EOF'''

task_events_csv_colnames = ['iat','duration','cpu','memory', 'location']         
task_events_df = pd.read_csv(os.path.join('/root/k8s_google_injection', 'synthetic_trace_10000_with_cluster5.csv'), sep=',', header=None, index_col=False, 
                         names=task_events_csv_colnames)

request_log_colnames = ['timestamp', 'pod_name','duration', 'cpu', 'memory', 'location']
request_log = pd.DataFrame(columns=request_log_colnames)

# Run for 1 hours

test_duration = 1 * 60 * 60
finish_time = time.time() + test_duration

print("Experiment started running at: " + str(time.time()))
for index, row in task_events_df.iterrows():
    if index <= 1209:
        #if int(row['iat']/10) > 1 and int(row['iat']/10) < 2 * 60:
        if int(row['iat']/10) <= 1 * 60:
            pod_name = "task" + str(index)
            cpu_request = int(10000.0*row['cpu'])
            memory_request = int(10000.0*row['memory'])
            duration = row['duration']/1000000
            location = row['location']
            sleep_arg = 'sleep ' + str(duration)
            command = '/bin/bash -c \'' + sleep_arg + '\''

            print("Sleep for " + str(row['iat']/10.0) + " seconds ...")
            time.sleep(row['iat']/10.0)
            memory_request_byte = memory_request*1048576

            # if float(duration) < test_duration:
            command_create = job_template.format(job_name=pod_name, job_duration=duration, memory_req=memory_request, cpu_req=cpu_request, location=location)
            # else:
            #     pod_name = "deployment" + str(index)
            #     command_create = deployment_template.format(deployment_name=pod_name, memory_req=memory_request, cpu_req=cpu_request, location=location)
            timestamp = time.time()
            os.system(command_create)
            request_log = request_log.append([{'timestamp':timestamp, 'pod_name':pod_name, 'duration':duration, 
                                 'cpu':cpu_request, 'memory':memory_request, 'location': location}],ignore_index=True)
            #file_name = 'fog_scheduling_test_logs_' + str(time.time()) + '.csv' 
            file_name = 'multi_cluster_scheduling_logs.csv'
            request_log.to_csv(file_name)
    else:
        break
        
print("DONE!!! Finished running at: " + str(time.time()))
