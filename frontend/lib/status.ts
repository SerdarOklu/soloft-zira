import type { JobStatus, SourceStatus } from './types';

/**
 * UDS maps status words to badge tones (STATUS_TONES). These are the words that give the
 * tone Zira wants: a source that is simply not connected yet is neutral, not an error.
 */
export const SOURCE_BADGE: Record<SourceStatus, string> = {
  ok: 'connected',
  error: 'failed',
  never_fetched: 'pending',
  not_connected: 'closed',
};

export const JOB_BADGE: Record<JobStatus, string> = {
  queued: 'pending',
  running: 'in_progress',
  done: 'done',
  failed: 'failed',
};

export const isActive = (status: JobStatus): boolean => status === 'queued' || status === 'running';
