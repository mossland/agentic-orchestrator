import { expect } from "chai";
import { ethers } from "hardhat";

describe("MOCVolatilityHedgeDAO", function () {
  let MOCVolatilityHedgeDAO: any;
  let mocVolatilityHedgeDaoInstance: any;
  let owner: any, user1: any;

  beforeEach(async () => {
    const [deployer, addr1] = await ethers.getSigners();
    owner = deployer;
    user1 = addr1;

    MOCVolatilityHedgeDAO = await ethers.getContractFactory("MOCVolatilityHedgeDAO");
    mocVolatilityHedgeDaoInstance = await MOCVolatilityHedgeDAO.deploy();
  });

  describe("Deployment", function () {
    it("Should set the right owner", async function () {
      expect(await mocVolatilityHedgeDaoInstance.owner()).to.equal(owner.address);
    });
  });

  describe("Insurance Policies", function () {
    let policyId: any;

    beforeEach(async () => {
      const tx = await mocVolatilityHedgeDaoInstance.createPolicy(100, 200, "ETH/USD");
      const receipt = await tx.wait();
      const event = receipt.events?.find((event) => event.event === "PolicyCreated");
      policyId = event?.args?.policyId;
    });

    it("Should create a new insurance policy", async function () {
      expect(policyId).to.be.properBN;
    });

    it("Should allow the owner to update the policy conditions", async function () {
      await mocVolatilityHedgeDaoInstance.connect(owner).updatePolicyConditions(policyId, 150);
      const policy = await mocVolatilityHedgeDaoInstance.policies(policyId);
      expect(policy.threshold).to.equal(ethers.utils.parseEther("150"));
    });

    it("Should revert if a non-owner tries to update the policy conditions", async function () {
      await expect(mocVolatilityHedgeDaoInstance.connect(user1).updatePolicyConditions(policyId, 150))
        .to.be.revertedWith("Ownable: caller is not the owner");
    });

    it("Should trigger payouts based on predefined market conditions", async function () {
      // Mock real-time price data for testing
      const mockPrice = ethers.utils.parseEther("250"); // Above threshold
      await mocVolatilityHedgeDaoInstance.connect(owner).setMockPrice(mockPrice);
      await mocVolatilityHedgeDaoInstance.triggerPayouts();
      expect(await mocVolatilityHedgeDaoInstance.policies(policyId)).to.have.property('payoutTriggered', true);
    });
  });

  describe("Access Control", function () {
    it("Should revert if a non-owner tries to create a policy", async function () {
      await expect(mocVolatilityHedgeDaoInstance.connect(user1).createPolicy(100, 200, "ETH/USD"))
        .to.be.revertedWith("Ownable: caller is not the owner");
    });

    it("Should revert if a non-owner tries to set mock price", async function () {
      await expect(mocVolatilityHedgeDaoInstance.connect(user1).setMockPrice(ethers.utils.parseEther("250")))
        .to.be.revertedWith("Ownable: caller is not the owner");
    });
  });

  describe("Edge Cases and Reverts", function () {
    it("Should revert if trying to create a policy with invalid parameters", async function () {
      await expect(mocVolatilityHedgeDaoInstance.createPolicy(0, 100, "ETH/USD"))
        .to.be.revertedWith("Invalid threshold or premium");
    });

    it("Should not trigger payout if market conditions are not met", async function () {
      const mockPrice = ethers.utils.parseEther("150"); // Below threshold
      await mocVolatilityHedgeDaoInstance.connect(owner).setMockPrice(mockPrice);
      await mocVolatilityHedgeDaoInstance.triggerPayouts();
      expect(await mocVolatilityHedgeDaoInstance.policies(policyId)).to.have.property('payoutTriggered', false);
    });
  });
});