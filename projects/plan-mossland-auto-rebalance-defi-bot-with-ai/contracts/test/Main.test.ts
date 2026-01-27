import { HardhatRuntimeEnvironment } from "hardhat/types";
import { DeployFunction } from "hardhat-deploy/types";
import { ethers } from "ethers";

const deployPlan: DeployFunction = async function (hre: HardhatRuntimeEnvironment) {
  const { deployments, getNamedAccounts } = hre;
  const { deploy } = deployments;

  const { deployer } = await getNamedAccounts();

  await deploy("AutoRebalanceBot", {
    from: deployer,
    args: [],
    log: true,
  });
};

export default deployPlan;
deployPlan.tags = ["AutoRebalanceBot"];

import { AutoRebalanceBot } from "../typechain-types";
import { expect } from "chai";

describe("AutoRebalanceBot Tests", function () {
  let autoRebalanceBot: AutoRebalanceBot;

  beforeEach(async function () {
    const [owner, otherAccount] = await ethers.getSigners();
    const AutoRebalanceBotFactory = await ethers.getContractFactory("AutoRebalanceBot");
    autoRebalanceBot = (await AutoRebalanceBotFactory.deploy()) as AutoRebalanceBot;
    await autoRebalanceBot.deployed();
  });

  describe("Deployment", function () {
    it("Should set the right owner", async function () {
      const [owner] = await ethers.getSigners();
      expect(await autoRebalanceBot.owner()).to.equal(owner.address);
    });
  });

  describe("Public Functions", function () {
    it("should allow the owner to call rebalancePortfolio", async function () {
      const [owner, otherAccount] = await ethers.getSigners();
      const tx = await autoRebalanceBot.connect(owner).rebalancePortfolio();
      expect(tx).to.emit(autoRebalanceBot, "Rebalanced");
    });

    it("should not allow non-owner to call rebalancePortfolio", async function () {
      const [owner, otherAccount] = await ethers.getSigners();
      await expect(autoRebalanceBot.connect(otherAccount).rebalancePortfolio()).to.be.revertedWith("Ownable: caller is not the owner");
    });

    it("should update risk level when setRiskLevel is called", async function () {
      const [owner, otherAccount] = await ethers.getSigners();
      await autoRebalanceBot.connect(owner).setRiskLevel(5);
      expect(await autoRebalanceBot.riskLevel()).to.equal(5);
    });

    it("should not allow non-owner to call setRiskLevel", async function () {
      const [owner, otherAccount] = await ethers.getSigners();
      await expect(autoRebalanceBot.connect(otherAccount).setRiskLevel(10)).to.be.revertedWith("Ownable: caller is not the owner");
    });
  });

  describe("Edge Cases and Reverts", function () {
    it("should revert when setting risk level to an invalid value", async function () {
      const [owner, otherAccount] = await ethers.getSigners();
      await expect(autoRebalanceBot.connect(owner).setRiskLevel(101)).to.be.revertedWith("Invalid risk level");
    });
  });
});