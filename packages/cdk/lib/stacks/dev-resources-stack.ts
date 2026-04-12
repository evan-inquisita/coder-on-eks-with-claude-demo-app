import * as cdk from 'aws-cdk-lib';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as kms from 'aws-cdk-lib/aws-kms';
import * as s3 from 'aws-cdk-lib/aws-s3';
import { Construct } from 'constructs';

export interface DevResourcesStackProps extends cdk.StackProps {
  /** ARN of the workspace IRSA role created by coder-and-claude-on-eks-demo-infra. */
  workspaceIrsaRoleArn: string;
}

export class DevResourcesStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: DevResourcesStackProps) {
    super(scope, id, props);

    // ── KMS key for document encryption ──
    const documentsKey = new kms.Key(this, 'DocumentsKey', {
      enableKeyRotation: true,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      alias: 'demo-doc-chat-documents-key',
      description: 'KMS key for demo doc-chat documents bucket',
    });

    // ── Documents bucket (uploaded PDFs) ──
    const documentsBucket = new s3.Bucket(this, 'DocumentsBucket', {
      bucketName: `demo-doc-chat-documents-${this.account}`,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      encryption: s3.BucketEncryption.KMS,
      encryptionKey: documentsKey,
      enforceSSL: true,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
    });

    // ── PR assets bucket (screenshots embedded in PR descriptions) ──
    const prAssetsBucket = new s3.Bucket(this, 'PrAssetsBucket', {
      bucketName: `demo-doc-chat-pr-assets-${this.account}`,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      enforceSSL: true,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
    });

    // ── Access role trusted by the workspace IRSA role ──
    const accessRole = new iam.Role(this, 'DocChatAccessRole', {
      roleName: 'demo-doc-chat-dev-access-role',
      assumedBy: new iam.ArnPrincipal(props.workspaceIrsaRoleArn),
      description: 'Role assumed by Coder workspace IRSA to access doc-chat dev resources',
    });

    accessRole.addToPolicy(
      new iam.PolicyStatement({
        actions: [
          's3:GetObject',
          's3:PutObject',
          's3:DeleteObject',
          's3:ListBucket',
          's3:PutObjectTagging',
          's3:GetObjectTagging',
        ],
        resources: [
          documentsBucket.bucketArn,
          documentsBucket.arnForObjects('*'),
          prAssetsBucket.bucketArn,
          prAssetsBucket.arnForObjects('*'),
        ],
      })
    );

    accessRole.addToPolicy(
      new iam.PolicyStatement({
        actions: ['kms:Encrypt', 'kms:Decrypt', 'kms:GenerateDataKey', 'kms:DescribeKey'],
        resources: [documentsKey.keyArn],
      })
    );

    accessRole.addToPolicy(
      new iam.PolicyStatement({
        actions: ['bedrock:InvokeModel', 'bedrock:InvokeModelWithResponseStream'],
        resources: ['*'],
      })
    );

    accessRole.addToPolicy(
      new iam.PolicyStatement({
        actions: ['secretsmanager:GetSecretValue'],
        resources: [`arn:aws:secretsmanager:*:${this.account}:secret:demo-workspace/*`],
      })
    );

    // ── Outputs ──
    new cdk.CfnOutput(this, 'DocumentsBucketName', { value: documentsBucket.bucketName });
    new cdk.CfnOutput(this, 'PrAssetsBucketName', { value: prAssetsBucket.bucketName });
    new cdk.CfnOutput(this, 'AccessRoleArn', { value: accessRole.roleArn });
    new cdk.CfnOutput(this, 'DocumentsKeyArn', { value: documentsKey.keyArn });
  }
}
