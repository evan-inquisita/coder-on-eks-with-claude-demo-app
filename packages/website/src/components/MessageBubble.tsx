import React from 'react';
import type { Message } from '../types';

interface Props {
  message: Message;
}

export function MessageBubble({ message }: Props): React.ReactElement {
  return (
    <div className={`bubble bubble-${message.role}`}>
      <div className="bubble-role">{message.role}</div>
      <div className="bubble-content">{message.content}</div>
    </div>
  );
}
