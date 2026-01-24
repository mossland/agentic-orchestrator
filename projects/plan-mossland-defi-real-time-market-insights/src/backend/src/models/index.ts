import { Entity, PrimaryGeneratedColumn, Column, OneToMany } from 'typeorm';

@Entity()
export class User {
  @PrimaryGeneratedColumn()
  id: number;

  @Column()
  username: string;

  @OneToMany(() => SentimentAnalysis, sentiment => sentiment.user)
  sentiments: SentimentAnalysis[];

  @Column({ type: 'timestamp', default: () => 'CURRENT_TIMESTAMP' })
  created_at: Date;

  @Column({ type: 'timestamp', default: () => 'CURRENT_TIMESTAMP', onUpdate: 'CURRENT_TIMESTAMP' })
  updated_at: Date;
}

@Entity()
export class SentimentAnalysis {
  @PrimaryGeneratedColumn()
  id: number;

  @Column()
  sentiment: string;

  @Column('text')
  tweet_content: string;

  @ManyToOne(() => User, user => user.sentiments)
  user: User;

  @Column({ type: 'timestamp', default: () => 'CURRENT_TIMESTAMP' })
  created_at: Date;

  @Column({ type: 'timestamp', default: () => 'CURRENT_TIMESTAMP', onUpdate: 'CURRENT_TIMESTAMP' })
  updated_at: Date;
}

@Entity()
export class BlockchainTransaction {
  @PrimaryGeneratedColumn()
  id: number;

  @Column('text')
  transaction_hash: string;

  @Column('text')
  blockchain_network: string;

  @OneToMany(() => User, user => user.transactions)
  users: User[];

  @Column({ type: 'timestamp', default: () => 'CURRENT_TIMESTAMP' })
  created_at: Date;

  @Column({ type: 'timestamp', default: () => 'CURRENT_TIMESTAMP', onUpdate: 'CURRENT_TIMESTAMP' })
  updated_at: Date;
}