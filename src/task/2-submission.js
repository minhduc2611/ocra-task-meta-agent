import { storeFile } from '../helpers.js';
import { getOrcaClient } from '@_koii/task-manager/extensions';
import { namespaceWrapper, TASK_ID } from '@_koii/namespace-wrapper';
import { createHash } from 'crypto';

export async function submission(roundNumber) {
  /**
   * Retrieve the task proofs from your container and submit for auditing
   * Must return a string of max 512 bytes to be submitted on chain
   * The default implementation handles uploading the proofs to IPFS
   * and returning the CID
   */
  console.log(`FETCH SUBMISSION FOR ROUND ${roundNumber}`);
  try {
    const orcaClient = await getOrcaClient();
    const result = await orcaClient.podCall(`submission/${roundNumber}`);

    const submission = result.data;

    // if you are writing a KPL task, use namespaceWrapper.getSubmitterAccount("KPL");
    const stakingKeypair = await namespaceWrapper.getSubmitterAccount();
    const stakingKey = stakingKeypair.publicKey.toBase58();

    // sign the submission
    const signature = await namespaceWrapper.payloadSigning(
      {
        taskId: TASK_ID,
        roundNumber: roundNumber,
        stakingKey: stakingKey,
        ...submission,
      },
      stakingKeypair.secretKey,
    );

    // store the submission on IPFS
    const cid = await storeFile({ signature }, 'submission.json');
    console.log('SUBMISSION CID:', cid);
    return cid;
  } catch (error) {
    console.error('FETCH SUBMISSION ERROR:', error);
  }
}
