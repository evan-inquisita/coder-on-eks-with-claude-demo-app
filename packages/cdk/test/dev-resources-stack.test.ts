// packages/cdk/test/dev-resources-stack.test.ts
import * as cdk from 'aws-cdk-lib';
import { Match, Template } from 'aws-cdk-lib/assertions';
import { DevResourcesStack } from '../lib/stacks/dev-resources-stack';

describe('DevResourcesStack', () => {
  function build(): Template {
    const app = new cdk.App();
    const stack = new DevResourcesStack(app, 'TestDocChatDevResources', {
      env: { account: '111111111111', region: 'us-east-1' },
      workspaceIrsaRoleArn: 'arn:aws:iam::111111111111:role/workspace-irsa-role',
    });
    return Template.fromStack(stack);
  }

  test('creates KMS key with rotation enabled', () => {
    const template = build();
    template.resourceCountIs('AWS::KMS::Key', 1);
    template.hasResourceProperties('AWS::KMS::Key', {
      EnableKeyRotation: true,
    });
  });

  test('creates two S3 buckets (documents and pr-assets), both KMS-encrypted documents and SSL-enforced', () => {
    const template = build();
    template.resourceCountIs('AWS::S3::Bucket', 2);
    template.hasResourceProperties('AWS::S3::Bucket', {
      BucketName: Match.stringLikeRegexp('^demo-doc-chat-documents-'),
      BucketEncryption: {
        ServerSideEncryptionConfiguration: Match.arrayWith([
          Match.objectLike({
            ServerSideEncryptionByDefault: Match.objectLike({ SSEAlgorithm: 'aws:kms' }),
          }),
        ]),
      },
    });
    template.hasResourceProperties('AWS::S3::Bucket', {
      BucketName: Match.stringLikeRegexp('^demo-doc-chat-pr-assets-'),
    });
  });

  test('creates access role trusted by the workspace IRSA role', () => {
    const template = build();
    template.hasResourceProperties('AWS::IAM::Role', {
      RoleName: 'demo-doc-chat-dev-access-role',
      AssumeRolePolicyDocument: Match.objectLike({
        Statement: Match.arrayWith([
          Match.objectLike({
            Action: 'sts:AssumeRole',
            Principal: Match.objectLike({
              AWS: 'arn:aws:iam::111111111111:role/workspace-irsa-role',
            }),
          }),
        ]),
      }),
    });
  });

  test('access role has Bedrock invoke permissions', () => {
    const template = build();
    template.hasResourceProperties('AWS::IAM::Policy', {
      PolicyDocument: Match.objectLike({
        Statement: Match.arrayWith([
          Match.objectLike({
            Action: Match.arrayWith(['bedrock:InvokeModel']),
            Resource: '*',
          }),
        ]),
      }),
    });
  });

});
